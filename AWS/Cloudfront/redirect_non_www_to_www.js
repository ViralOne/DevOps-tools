function objectToQueryString(obj) {
    var str = [];
    for (var param in obj)
        if (obj[param].value == '') 
            str.push(encodeURIComponent(param));
        else 
            str.push(encodeURIComponent(param) + "=" + encodeURIComponent(obj[param].value));   
        
    return str.join("&");
}

function handler(event) {
    var request = event.request;
    var uri = request.uri;
    var loc = "";


    // Extract the Host header to get the domain
    var hostHeader = request.headers['host'];
    var newdomain = hostHeader.value;

    // Hardcode domain name
    // var newdomain = 'staging.mydomain.com';

    if (Object.keys(request.querystring).length) 
        loc = `https://www.${newdomain}${uri}?${objectToQueryString(request.querystring)}`
    else 
        loc = `https://www.${newdomain}${uri}`

    var response = {
        statusCode: 302,
        statusDescription: 'Found',
        headers: {
            'location': { value: `${loc}` }      
        }
    };
    return response;
}
