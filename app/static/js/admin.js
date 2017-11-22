/**
 * Created by Administrator on 2017/11/21 0021.
 */
(function() {
    var clickEvent = function(el1, el2) {
        el1.onclick = function() {
            if (el2.style.display === 'none') {
                el2.style.display = 'block';
            } else {
                el2.style.display = 'none';
            }
        }
    }

    // flash message div
    var flashDiv = document.getElementsByClassName('flash-msg')[0];
    var flashX = document.getElementsByClassName('flash-x')[0];

    clickEvent(flashX, flashDiv);
})();
