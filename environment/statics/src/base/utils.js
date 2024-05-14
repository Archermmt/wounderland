export default function jsonRequest(url, data, callback) {
    var xobj = new XMLHttpRequest();
    xobj.overrideMimeType("application/json");
    xobj.onreadystatechange = function () {
        if (xobj.readyState == XMLHttpRequest.DONE) {
            const response = JSON.parse(xobj.responseText);
            callback(response);
        }
    }
    xobj.open('POST', url, true);
    xobj.send(JSON.stringify(data));
}
