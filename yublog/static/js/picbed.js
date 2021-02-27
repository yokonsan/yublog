/**
 * Created by Administrator on 2018/5/15 0015.
 */
function showIpt(btn) {
    let btn = btn;
    let uploadIpt = document.getElementsByClassName('upload-input')[0];
    if (btn.innerText === '上传') {
        btn.innerText = '取消';
        uploadIpt.style.display = 'block';
    } else {
        btn.innerText = '上传';
        uploadIpt.style.display = 'none';
    }
}

function initAjax(method, url, data) {
    let request;
    if (window.XMLHttpRequest) {
        request = new XMLHttpRequest();
    } else {
        request = new ActiveXObject('Microsoft.XMLHTTP');
    }

    request.onreadystatechange = function () { // 状态发生变化时，函数被回调
        if (request.readyState === 4) { // 成功完成
            // 判断响应结果:
            if (request.status === 200) {
                // 成功，通过responseText拿到响应的文本:
                return success();
            } else {
                // 失败，根据响应码判断失败原因:
                return fail();
            }
        } else {
            // HTTP请求还在继续...
        }
    };
    request.open(method, url);
    request.setRequestHeader('Content-Type', 'application/json');
    request.send(data);
}

function renameImg(btn) {
    let img = btn.parentNode.parentNode.getElementsByClassName('img-name')[0];
    // console.log(img)
    let imgKey = img.innerText;
    let name=prompt("请输入新的图片名", imgKey);
    if (name !== null && name !== "") {
        data = JSON.stringify({
            key: imgKey,
            keyTo: name
        });
        initAjax('POST', '/admin/qiniu/rename', data);
        location.reload();
    } else {
        // ...
    }

}

function deleteImg(btn) {
    let img = btn.parentNode.parentNode.getElementsByClassName('img-name')[0];
    let imgKey = img.innerText;

    if (confirm("你确定删除吗？")) {
        data = JSON.stringify({
            key: imgKey
        });
        initAjax('POST', '/admin/qiniu/delete', data);
        location.reload();
    }
    else {
        // ...
    }
}

