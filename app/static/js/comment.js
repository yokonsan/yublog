/**
 * Created by Administrator on 2017/12/28 0028.
 */
(function() {
    var commentChildren = document.getElementsByClassName('comment-children');
    var childrenLi;
    for (var c=0; c<commentChildren.length; c++) {
        childrenLi = commentChildren[c].getElementsByTagName('li');
        for (var l=0; l<childrenLi.length; l++) {
            var childrenName = childrenLi[l].getElementsByClassName('comment-name')[0];
            var childrenReply = childrenLi[l].getElementsByClassName('reply-comment')[0];
            var childrenTime = childrenLi[l].getElementsByClassName('comment-time')[0];

            childrenLi[l].onmouseenter = function() {
                childrenName.style.display = "block";
                childrenReply.style.display = "block";
            };
            childrenLi[l].onmouseleave = function() {
                childrenName.style.display = "none";
                childrenReply.style.display = "none";
            }
        }
    }
    // 回复按钮
    var commentCon = document.getElementById('comments');
    var commentIpt = document.getElementsByClassName('comment-send')[0];
    var replyBtns = commentCon.getElementsByClassName('comment-reply-link');

    for (var b=0; b<replyBtns.length; b++) {
        replyBtns[b].onclick = function() {
            var replyId = this.attributes["replyid"].value;
            var replyTo = this.attributes["replyto"].value;
            var comment = document.getElementById(replyId);
            var cancel = commentIpt.getElementsByClassName('cancel')[0];
            var submitBtn = commentIpt.getElementsByClassName('comment-submit')[0];

            submitBtn.attributes["replyid"].value = replyId;
            submitBtn.attributes["replyto"].value = replyTo;
            cancel.style.display = 'inline-block';
            comment.appendChild(commentIpt);
        }
    }

    // 取消按钮
    var cancel = commentIpt.getElementsByClassName('cancel')[0];
    cancel.onclick = function() {
        var cancelPar = cancel.parentElement.parentElement.parentElement.parentElement;
        var submitBtn = commentIpt.getElementsByClassName('comment-submit')[0];

        submitBtn.attributes["replyid"].value = "";
        submitBtn.attributes["replyto"].value = "";
        cancel.style.display = 'none';

        cancelPar.removeChild(commentIpt);
        commentCon.appendChild(commentIpt);
    };

    function success() {
        var text = document.getElementsByClassName('comment-list')[0];
        var msg = '<li class="comment">评论将在通过后展示...</li>';

        text.appendChild(msg);
    }

    function fail() {
        var text = document.getElementsByClassName('comment-list')[0];
        var msg = '<li class="comment">发布评论失败...</li>';

        text.appendChild(msg);
    }
    // 发布按钮
    var submitBtn = commentIpt.getElementsByClassName('comment-submit')[0];
    submitBtn.onclick = function() {
        var replyId = this.attributes["replyid"].value;
        var replyTo = this.attributes["replyto"].value;
        var postId = this.attributes["postid"].value;
        postClick(postId, replyId, replyTo);
    };

    function postClick(id, replyId, replyName) {
        var request;
        if (window.XMLHttpRequest) {
            request = new XMLHttpRequest();
        } else {
            request = new ActiveXObject('Microsoft.XMLHTTP');
        }
        // form
        var comForm = commentCon.getElementsByClassName('textarea-container')[0];
        var userIpt = comForm.getElementsByTagName('input')[0];
        var emailIpt = comForm.getElementsByTagName('input')[1];
        var websiteIpt = comForm.getElementsByTagName('input')[2];
        var textarea = comForm.getElementsByTagName('textarea')[0];

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
        if (replyId) {
            request.open('POST', '/'+ id +'/comment');
            request.setRequestHeader('Content-Type', 'application/json');
            FormData= JSON.stringify({
                nickname: userIpt.value,
                email: emailIpt.value,
                website: websiteIpt.value,
                comment: '@' + ' ' + replyName + '：' + textarea.value,
                isReply: true,
                replyTo: replyId
            });
            request.send(FormData);
        } else {
            request.open('POST', '/'+ id +'/comment');
            request.setRequestHeader('Content-Type', 'application/json');
            FormData= JSON.stringify({
                nickname: userIpt.value,
                email: emailIpt.value,
                website: websiteIpt.value,
                comment: textarea.value
            });
            console.log(FormData);
            request.send(FormData);
        }
    }

})();

