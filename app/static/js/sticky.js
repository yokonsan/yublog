(function() {
    var root = (typeof self == 'object' && self.self == self && self) ||
        (typeof global == 'object' && global.global == global && global) ||
        this || {};

    var util = {
        extend: function(target) {
            for (var i = 1, len = arguments.length; i < len; i++) {
                for (var prop in arguments[i]) {
                    if (arguments[i].hasOwnProperty(prop)) {
                        target[prop] = arguments[i][prop]
                    }
                }
            }

            return target
        },
        getStyle: function(element, prop) {
            return element.currentStyle ? element.currentStyle[prop] : document.defaultView.getComputedStyle(element)[prop]
        },
        getScrollOffsets: function() {
            var w = window;
            if (w.pageXOffset != null) return { x: w.pageXOffset, y: w.pageYOffset };
            var d = w.document;
            if (document.compatMode == "CSS1Compat") {
                return {
                    x: d.documentElement.scrollLeft,
                    y: d.documentElement.scrollTop
                }
            }
            return { x: d.body.scrollLeft, y: d.body.scrollTop }
        },
        addEvent: function(element, type, fn) {
            if (document.addEventListener) {
                element.addEventListener(type, fn, false);
                return fn;
            } else if (document.attachEvent) {
                var bound = function() {
                    return fn.apply(element, arguments)
                }
                element.attachEvent('on' + type, bound);
                return bound;
            }
        },
        indexOf: function(array, item) {
            if (array.indexOf) {
                return array.indexOf(item);
            } else {
                var result = -1;
                for (var i = 0, len = array.length; i < len; i++) {
                    if (array[i] === item) {
                        result = i;
                        break;
                    }
                }
                return result;
            }
        },
        addClass: function(element, className) {
            var classNames = element.className.split(/\s+/);
            if (util.indexOf(classNames, className) == -1) {
                classNames.push(className);
            }
            element.className = classNames.join(' ')
        },
        removeClass: function(element, className) {
            var classNames = element.className.split(/\s+/);
            var index = util.indexOf(classNames, className)
            if (index !== -1) {
                classNames.splice(index, 1);
            }
            element.className = classNames.join(' ')
        },
        isValidListener: function(listener) {
            if (typeof listener === 'function') {
                return true
            } else if (listener && typeof listener === 'object') {
                return util.isValidListener(listener.listener)
            } else {
                return false
            }
        },
        removeProperty: function(element, name) {
            if (element.style.removeProperty) {
                element.style.removeProperty(name);
            } else {
                element.style.removeAttribute(name);
            }
        }
    };

    function EventEmitter() {
        this.__events = {}
    }

    EventEmitter.prototype.on = function(eventName, listener) {
        if (!eventName || !listener) return;

        if (!util.isValidListener(listener)) {
            throw new TypeError('listener must be a function');
        }

        var events = this.__events;
        var listeners = events[eventName] = events[eventName] || [];
        var listenerIsWrapped = typeof listener === 'object';

        // 不重复添加事件
        if (util.indexOf(listeners, listener) === -1) {
            listeners.push(listenerIsWrapped ? listener : {
                listener: listener,
                once: false
            });
        }

        return this;
    };

    EventEmitter.prototype.once = function(eventName, listener) {
        return this.on(eventName, {
            listener: listener,
            once: true
        })
    };

    EventEmitter.prototype.off = function(eventName, listener) {
        var listeners = this.__events[eventName];
        if (!listeners) return;

        var index;
        for (var i = 0, len = listeners.length; i < len; i++) {
            if (listeners[i] && listeners[i].listener === listener) {
                index = i;
                break;
            }
        }

        if (typeof index !== 'undefined') {
            listeners.splice(index, 1, null)
        }

        return this;
    };

    EventEmitter.prototype.emit = function(eventName, args) {
        var listeners = this.__events[eventName];
        if (!listeners) return;

        for (var i = 0; i < listeners.length; i++) {
            var listener = listeners[i];
            if (listener) {
                listener.listener.apply(this, args || []);
                if (listener.once) {
                    this.off(eventName, listener.listener)
                }
            }

        }

        return this;

    };

    function Sticky(element, options) {
        EventEmitter.call(this);
        this.element = typeof element === "string" ? document.querySelector(element) : element;
        this.options = util.extend({}, this.constructor.defaultOptions, options)
        this.init();
    }

    Sticky.version = '1.0.0';

    Sticky.defaultOptions = {
        offset: 0
    }

    var proto = Sticky.prototype = new EventEmitter();

    proto.constructor = Sticky;

    proto.init = function() {

        this.calculateElement();

        this.bindScrollEvent();
    };

    proto.calculateElement = function() {
        // 计算出元素距离文档的位置
        if (this.element) {
            var rect = this.element.getBoundingClientRect();
            this.eLeft = rect.left + util.getScrollOffsets().x;
            this.eTop = rect.top + util.getScrollOffsets().y - this.options.offset;
        }
    };

    proto.bindScrollEvent = function() {
        var self = this;

        util.addEvent(window, "scroll", function(event) {
            if (util.getScrollOffsets().y > self.eTop) {
                self.setSticky();
            } else {
                self.setNormal();
            }
        })
    };

    proto.setSticky = function() {
        if (this.status == "sticky") return;
        this.status = "sticky";
        util.addClass(this.element, 'sticky');
        this.setElementSticky();
        this.emit("onStick");
    };

    proto.setNormal = function() {
        if (this.status !== "sticky") return;
        this.status = "normal";
        util.removeClass(this.element, 'sticky');
        this.setElementNormal();
        this.emit("onDetach");
    };

    proto.setElementSticky = function() {
        this.element.style.position = "fixed";
        this.element.style.width = '240px';
        this.element.style.top = this.options.offset + 'px';
    };

    proto.setElementNormal = function() {
        util.removeProperty(this.element, "position")
        util.removeProperty(this.element, "width")
        util.removeProperty(this.element, "top")
    };

    if (typeof exports != 'undefined' && !exports.nodeType) {
        if (typeof module != 'undefined' && !module.nodeType && module.exports) {
            exports = module.exports = Sticky;
        }
        exports.Sticky = Sticky;
    } else {
        root.Sticky = Sticky;
    }
}());