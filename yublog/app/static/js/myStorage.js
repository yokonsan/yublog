/**
 * Created by Administrator on 2017/12/30 0030.
 */
// 封装localStorage
(function() {
    window.ms = {
        set: set,
        get: get,
        remove:remove
    };

    function set(key, val) {
        localStorage.setItem(key, JSON.stringify(val));
    }

    function get(key) {
        var json = localStorage.getItem(key);
        if (json) {
            return JSON.parse(json);
        }
    }

    function remove(key) {
        localStorage.removeItem(key);
    }
})();