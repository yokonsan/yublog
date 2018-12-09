/**
 * Created by Administrator on 2017/11/21 0021.
 */

function flashEvent() {
    // flash message div
    let flashDiv = document.getElementsByClassName('flash-msg')[0];
    let flashX = document.getElementsByClassName('flash-x')[0];

    flashDiv.style.display = 'none';
}

function firm(url) {
    let request;
    if (window.XMLHttpRequest) {
        request = new XMLHttpRequest();
    } else {
        request = new ActiveXObject('Microsoft.XMLHTTP');
    }
    //利用对话框返回的值 （true 或者 false）
    if (confirm("你确定删除吗？")) {
        // 发送请求:
        request.open('GET', url);
        request.send();
        location.reload();
    }
    else { }

}
