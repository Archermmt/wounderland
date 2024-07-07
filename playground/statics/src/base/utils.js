export function jsonRequest(url, data, callback) {
    var xobj = new XMLHttpRequest();
    xobj.overrideMimeType("application/json");
    xobj.onreadystatechange = function () {
        if (xobj.readyState == XMLHttpRequest.DONE) {
            const response = JSON.parse(xobj.responseText);
            if (response.success) {
                callback(response.info);
            } else {
                console.log("Request to " + url + " failed: " + response.error);
            }
        }
    }
    xobj.open('POST', url, true);
    xobj.send(JSON.stringify(data));
}

export function textBlock(dict, space = 1) {
    let lines = [];
    for (const [key, info] of Object.entries(dict)) {
        let line = "";
        for (let i = 0; i < space; i++) {
            line += "-";
        }
        line += key;
        if (info.constructor == Object) {
            lines.push(line);
            lines.push(...textBlock(info, space + 1));
        } else {
            line += ": " + info;
            lines.push(line);
        }
    }
    return lines;
}

export function recursiveUpdate(base_dict, new_dict) {
    if (!base_dict) {
        return new_dict;
    }
    if (!new_dict) {
        return base_dict;
    }
    let clone_base_dict = JSON.parse(JSON.stringify(base_dict));
    for (const [key, info] of Object.entries(new_dict)) {
        if (key in clone_base_dict) {
            if (clone_base_dict[key].constructor == Object && info.constructor == Object) {
                clone_base_dict[key] = recursiveUpdate(clone_base_dict[key], info);
            } else {
                clone_base_dict[key] = info;
            }
        } else {
            clone_base_dict[key] = info;
        }
    }
    return clone_base_dict;
}

export default { jsonRequest, textBlock, recursiveUpdate }