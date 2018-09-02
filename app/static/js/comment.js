/**
 * Created by Administrator on 2017/12/28 0028.
 */
(function() {
    // form
    let commentCon = document.getElementById('comments');
    let comForm = commentCon.getElementsByClassName('textarea-container')[0];
    let userIpt = comForm.getElementsByTagName('input')[0];
    let emailIpt = comForm.getElementsByTagName('input')[1];
    let websiteIpt = comForm.getElementsByTagName('input')[2];
    let textarea = comForm.getElementsByTagName('textarea')[0];
    let authorInfo = commentCon.getElementsByClassName('author-info')[0];
    let inputDiv = authorInfo.getElementsByClassName('input-div');
    let loginUser = commentCon.getElementsByClassName('logined')[0];
    // 判断本地是否有登录记录
    let user = ms.get('user');
    if (user) {
        userIpt.value = user.nickname;
        emailIpt.value = user.email;
        websiteIpt.value = user.website;
        authorInfo.style.display = "none";
        loginUser.style.display = "block";
    }
    let deleteUser = loginUser.getElementsByClassName('delete-user')[0];
    if (deleteUser) {
        deleteUser.onclick = function() {
            ms.remove('user');
            loginUser.style.display = "none";
            authorInfo.style.display = "block";
        };
    }
    // 本地存储用户
    function saveUser(key, val) {
        if (!ms.get(user)) {
            ms.set(key, val);
        }
    }
    // 回复按钮
    let commentIpt = document.getElementsByClassName('comment-send')[0];
    let replyBtns = commentCon.getElementsByClassName('comment-reply-link');

    for (let b=0; b<replyBtns.length; b++) {
        replyBtns[b].onclick = function() {
            let currentId = this.attributes["curid"].value;
            let replyId = this.attributes["replyid"].value;
            let replyTo = this.attributes["replyto"].value;
            let comment = document.getElementById(currentId);
            let cancel = commentIpt.getElementsByClassName('cancel')[0];
            let submitBtn = commentIpt.getElementsByClassName('comment-submit')[0];

            submitBtn.attributes["replyid"].value = replyId;
            submitBtn.attributes["replyto"].value = replyTo;
            cancel.style.display = 'inline-block';
            comment.appendChild(commentIpt);
        }
    }

    // 取消按钮
    let cancel = commentIpt.getElementsByClassName('cancel')[0];
    // 表单复原
    function resetForm(ele) {
        let cancelPar = ele.parentElement.parentElement.parentElement;
        let submitBtn = commentIpt.getElementsByClassName('comment-submit')[0];

        submitBtn.attributes["replyid"].value = "";
        submitBtn.attributes["replyto"].value = "";
        cancel.style.display = 'none';

        cancelPar.removeChild(commentIpt);
        commentCon.appendChild(commentIpt);
    }
    cancel.onclick = function() {
        resetForm(cancel)
    };

    function success(key, val) {
        let text = document.getElementsByClassName('comment-list')[0];
        let msg = '<li class="comment" style="color: #df846c;">评论将在通过后展示...</li>';

        text.innerHTML+=msg;
    }

    function fail() {
        let text = document.getElementsByClassName('comment-list')[0];
        let msg = '<li class="comment" style="color: #df846c;">发布评论失败...</li>';

        text.innerHTML+=msg;
    }
    // 发布按钮
    let submitBtn = commentIpt.getElementsByClassName('comment-submit')[0];
    submitBtn.onclick = function() {
        let replyId = this.attributes["replyid"].value;
        let replyTo = this.attributes["replyto"].value;
        let postUrl = this.attributes["posturl"].value;
        let emailRe = /^(\w)+(\.\w+)*@(\w)+((\.\w+)+)$/;
        if (userIpt.value && emailIpt.value && textarea.value !== null && emailRe.test(emailIpt.value)) {
            resetForm(submitBtn);
            postClick(postUrl, replyId, replyTo);
        } else {
            alert('请正确填写必填项...')
        }

    };

    function postClick(url, replyId, replyName) {
        let request;
        if (window.XMLHttpRequest) {
            request = new XMLHttpRequest();
        } else {
            request = new ActiveXObject('Microsoft.XMLHTTP');
        }

        request.onreadystatechange = function () {
            if (request.readyState === 4) {
                if (request.status === 200) {
                    return success();
                } else {
                    return fail();
                }
            } else {

            }
        };
        if (replyId) {
            request.open('POST', '/'+ url +'/comment');
            request.setRequestHeader('Content-Type', 'application/json');
            nickname = userIpt.value;
            website = websiteIpt.value;
            textValue = textarea.value;
            FormData= JSON.stringify({
                nickname: nickname,
                email: emailIpt.value,
                website: website,
                comment: textValue,
                isReply: true,
                replyTo: replyId
            });
            let val1 = {nickname:userIpt.value,email: emailIpt.value,website: websiteIpt.value};
            saveUser('user', val1);
            request.send(FormData);
        } else {
            request.open('POST', '/'+ url +'/comment');
            request.setRequestHeader('Content-Type', 'application/json');
            FormData= JSON.stringify({
                nickname: userIpt.value,
                email: emailIpt.value,
                website: websiteIpt.value,
                comment: textarea.value
            });
            let val2 = {nickname:userIpt.value,email: emailIpt.value,website: websiteIpt.value};
            saveUser('user', val2);
            request.send(FormData);
        }
        textarea.value = "";
    }
})();

