#!/usr/bin/env bash
set -euo pipefail
export LC_NUMERIC=C

PROFILE="${AWS_PROFILE:-default}"
REGION="${AWS_REGION:-us-east-1}"
MAX_PARALLEL="${MAX_PARALLEL:-10}"

usage() {
  echo "Usage: AWS_PROFILE=prod $0 <command> [start] [end]"
  echo ""
  echo "Commands:"
  echo "  list                    List all Lambda functions"
  echo "  cost <indices|all>      Calculate cost for selected functions"
  echo ""
  echo "Examples:"
  echo "  AWS_PROFILE=prod $0 list"
  echo "  AWS_PROFILE=prod $0 cost all"
  echo "  AWS_PROFILE=prod $0 cost 0,1,5,10"
  echo "  AWS_PROFILE=prod $0 cost 5-15"
  echo "  AWS_PROFILE=prod $0 cost all 2026-01-01 2026-02-01"
  exit 1
}

[[ $# -lt 1 ]] && usage

CMD="$1"

fetch_functions() {
  aws lambda list-functions \
    --profile "$PROFILE" --region "$REGION" \
    --query 'Functions[*].[FunctionName,MemorySize,Architectures[0]]' \
    --output text | sort
}

if [[ "$CMD" == "list" ]]; then
  echo "Profile: $PROFILE | Region: $REGION"
  echo ""
  i=0
  fetch_functions | while IFS=$'\t' read -r name mem arch; do
    printf "  [%2d] %-60s %4sMB  %s\n" "$i" "$name" "$mem" "$arch"
    i=$((i + 1))
  done
  echo ""
  echo "Run: $0 cost <indices|all> [start] [end]"
  exit 0
fi

[[ "$CMD" != "cost" ]] && usage
[[ $# -lt 2 ]] && usage

SELECTION="$2"
START="${3:-$(date -v-1m +%Y-%m-01 2>/dev/null || date -d '1 month ago' +%Y-%m-01)}"
END="${4:-$(date +%Y-%m-01)}"

echo "Profile: $PROFILE | Region: $REGION | Period: $START → $END"
echo ""

# Load functions into arrays
declare -a fn_names fn_mems fn_archs
while IFS=$'\t' read -r name mem arch; do
  fn_names+=("$name")
  fn_mems+=("$mem")
  fn_archs+=("$arch")
done < <(fetch_functions)

# Resolve selection
declare -a sel_idx
if [[ "$SELECTION" == "all" ]]; then
  for i in "${!fn_names[@]}"; do sel_idx+=("$i"); done
else
  IFS=',' read -ra parts <<< "$SELECTION"
  for part in "${parts[@]}"; do
    part=$(echo "$part" | tr -d ' ')
    if [[ "$part" == *-* ]]; then
      IFS='-' read -r from to <<< "$part"
      for j in $(seq "$from" "$to"); do sel_idx+=("$j"); done
    else
      sel_idx+=("$part")
    fi
  done
fi

period=$(( ( $(date -jf %Y-%m-%d "$END" +%s 2>/dev/null || date -d "$END" +%s) - $(date -jf %Y-%m-%d "$START" +%s 2>/dev/null || date -d "$START" +%s) ) ))

# Temp dir for parallel results
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

echo "Fetching metrics for ${#sel_idx[@]} functions (${MAX_PARALLEL} parallel)..."
echo ""

# Launch all jobs in parallel, throttled
running=0
for i in "${sel_idx[@]}"; do
  i=$(echo "$i" | tr -d ' ')
  fn="${fn_names[$i]}"
  mem="${fn_mems[$i]}"
  arch="${fn_archs[$i]}"

  (
    inv=$(aws cloudwatch get-metric-statistics \
      --namespace AWS/Lambda --metric-name Invocations \
      --dimensions Name=FunctionName,Value="$fn" \
      --start-time "${START}T00:00:00Z" --end-time "${END}T00:00:00Z" \
      --period "$period" --statistics Sum \
      --profile "$PROFILE" --region "$REGION" \
      --query 'Datapoints[0].Sum' --output text 2>/dev/null)

    dur=$(aws cloudwatch get-metric-statistics \
      --namespace AWS/Lambda --metric-name Duration \
      --dimensions Name=FunctionName,Value="$fn" \
      --start-time "${START}T00:00:00Z" --end-time "${END}T00:00:00Z" \
      --period "$period" --statistics Average \
      --profile "$PROFILE" --region "$REGION" \
      --query 'Datapoints[0].Average' --output text 2>/dev/null)

    prov=$(aws lambda list-provisioned-concurrency-configs \
      --function-name "$fn" \
      --profile "$PROFILE" --region "$REGION" \
      --query 'ProvisionedConcurrencyConfigs[0].RequestedProvisionedConcurrentExecutions' \
      --output text 2>/dev/null)

    echo "${fn}|${mem}|${arch}|${inv}|${dur}|${prov}" > "$tmpdir/$i"
  ) &

  running=$((running + 1))
  if [[ $running -ge $MAX_PARALLEL ]]; then
    wait -n 2>/dev/null || wait
    running=$((running - 1))
  fi
done

wait

# Print results
printf "%-55s %10s %12s %6s %10s\n" "Function" "Invocations" "Avg Dur (ms)" "MB" "Est. Cost"
printf "%-55s %10s %12s %6s %10s\n" "--------" "-----------" "------------" "---" "---------"

total=0
for i in "${sel_idx[@]}"; do
  i=$(echo "$i" | tr -d ' ')
  [[ ! -f "$tmpdir/$i" ]] && continue

  IFS='|' read -r fn mem arch inv dur prov < "$tmpdir/$i"

  [[ "$inv" == "None" || -z "$inv" ]] && inv=0 && dur=0

  if [[ "$arch" == "arm64" ]]; then
    rate="0.0000133334"; prov_rate="0.0000041667"
  else
    rate="0.0000166667"; prov_rate="0.0000052083"
  fi

  cost=$(awk "BEGIN {
    gb = $mem / 1024; dur_s = $dur / 1000
    printf \"%.4f\", $inv * dur_s * gb * $rate + $inv * 0.0000002
  }")

  prov_cost=0; prov_note=""
  if [[ "$prov" != "None" && -n "$prov" && "$prov" != "0" ]]; then
    prov_cost=$(awk "BEGIN { printf \"%.4f\", $prov * ($mem / 1024) * $period * $prov_rate }")
    prov_note=" (+\$${prov_cost} prov)"
  fi

  line_total=$(awk "BEGIN { printf \"%.4f\", $cost + $prov_cost }")
  total=$(awk "BEGIN { printf \"%.4f\", $total + $line_total }")

  printf "%-55s %10.0f %12.1f %6s %10s\n" \
    "${fn:0:55}" "$inv" "$dur" "$mem" "\$${line_total}${prov_note}"
done

echo ""
printf "%86s \$%8s\n" "TOTAL:" "$total"
