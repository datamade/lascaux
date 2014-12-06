/*
 * Extends L.Map to synchronize the interaction on one map to one or more other maps.
 */

(function () {
    'use strict';

    L.Map = L.Map.extend({
        sync: function (map, options) {
            this._initSync();
            options = options || {};

            // prevent double-syncing the map:
            var present = false;
            this._syncMaps.forEach(function (other) {
                if (map === other) {
                    present = true;
                }
            });

            if (!present) {
                this._syncMaps.push(map);
            }

            if (!options.noInitialSync) {
                map.setView(this.getCenter(), {
                    animate: false,
                    reset: true
                });
            }
            return this;
        },

        // unsync maps from each other
        unsync: function (map) {
            var self = this;

            if (this._syncMaps) {
                this._syncMaps.forEach(function (synced, id) {
                    if (map === synced) {
                        self._syncMaps.splice(id, 1);
                    }
                });
            }

            return this;
        },

        // overload methods on originalMap to replay on _syncMaps;
        _initSync: function () {
            if (this._syncMaps) {
                return;
            }
            var originalMap = this;

            this._syncMaps = [];

            L.extend(originalMap, {
                setView: function (center, options, sync) {
                    if (!sync) {
                        originalMap._syncMaps.forEach(function (toSync) {
                            toSync.setView(center, options, true);
                        });
                    }
                    return L.Map.prototype.setView.call(this, center, options);
                },

                panBy: function (offset, options, sync) {
                    if (!sync) {
                        originalMap._syncMaps.forEach(function (toSync) {
                            toSync.panBy(offset, options, true);
                        });
                    }
                    return L.Map.prototype.panBy.call(this, offset, options);
                },

                _onResize: function (event, sync) {
                    if (!sync) {
                        originalMap._syncMaps.forEach(function (toSync) {
                            toSync._onResize(event, true);
                        });
                    }
                    return L.Map.prototype._onResize.call(this, event);
                }
            });

            originalMap.dragging._draggable._updatePosition = function () {
                L.Draggable.prototype._updatePosition.call(this);
                var self = this;
                originalMap._syncMaps.forEach(function (toSync) {
                    L.DomUtil.setPosition(toSync.dragging._draggable._element, self._newPos);
                    toSync.fire('moveend');
                });
            };
        }
    });
})();
