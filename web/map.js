(function () {
  const DEFAULT_CENTER = [120.15507, 30.274085];
  const params = new URLSearchParams(window.location.search);
  const apiKey = params.get("key") || "";
  const securityJsCode = params.get("securityJsCode") || "";
  const defaultZoom = Number(params.get("zoom") || 17);
  const lastLng = params.has("lastLng") ? Number(params.get("lastLng")) : NaN;
  const lastLat = params.has("lastLat") ? Number(params.get("lastLat")) : NaN;
  let theme = params.get("theme") === "dark" ? "dark" : "light";
  document.documentElement.dataset.theme = theme;

  function mapStyle() {
    return theme === "dark" ? "amap://styles/dark" : "amap://styles/normal";
  }

  function setTheme(value) {
    theme = value === "dark" ? "dark" : "light";
    document.documentElement.dataset.theme = theme;
    if (map) {
      map.setMapStyle(mapStyle());
    }
  }

  let bridge = null;
  let map = null;
  let currentMarker = null;
  let searchMarker = null;
  let selectedMarker = null;
  let placeSearch = null;
  let currentCityName = "杭州市";
  let pendingCurrentLocation = null;
  let pendingDefaultCenter = false;

  const statusEl = document.getElementById("mapStatus");
  const searchInput = document.getElementById("searchInput");
  const clearSearchButton = document.getElementById("clearSearchButton");
  const searchButton = document.getElementById("searchButton");
  const searchResults = document.getElementById("searchResults");
  const locateButton = document.getElementById("locateButton");

  function setStatus(message) {
    statusEl.textContent = message || "";
    if (bridge && message) {
      bridge.log(message);
    }
  }

  function initBridge() {
    return new Promise((resolve) => {
      if (!window.qt || !window.qt.webChannelTransport || !window.QWebChannel) {
        resolve(null);
        return;
      }
      new QWebChannel(window.qt.webChannelTransport, (channel) => {
        bridge = channel.objects.pinShiftBridge;
        resolve(bridge);
      });
    });
  }

  function loadAmap() {
    return new Promise((resolve, reject) => {
      if (!apiKey) {
        reject(new Error("高德地图 Key 未配置。"));
        return;
      }
      if (!securityJsCode) {
        reject(new Error("高德地图安全密钥未配置。"));
        return;
      }
      if (window.AMap) {
        resolve();
        return;
      }
      window._AMapSecurityConfig = {
        securityJsCode,
      };
      const script = document.createElement("script");
      script.src = `https://webapi.amap.com/maps?v=2.0&key=${encodeURIComponent(
        apiKey
      )}&plugin=AMap.PlaceSearch`;
      script.onload = resolve;
      script.onerror = () => reject(new Error("高德地图 JavaScript API 加载失败。"));
      document.head.appendChild(script);
    });
  }

  function createMarker(position, type) {
    const colors = {
      current: "#1a73e8",
      search: "#34a853",
      selected: "#d93025",
    };
    return new AMap.Marker({
      position,
      anchor: "bottom-center",
      content: `<div style="
        width: 18px;
        height: 18px;
        border-radius: 50%;
        background: ${colors[type]};
        border: 3px solid white;
        box-shadow: 0 2px 10px rgba(0,0,0,.28);
      "></div>`,
    });
  }

  function updateMarker(markerRef, position, type) {
    if (!markerRef) {
      markerRef = createMarker(position, type);
      map.add(markerRef);
    } else {
      markerRef.setPosition(position);
    }
    return markerRef;
  }

  function initMap() {
    const remembered = Number.isFinite(lastLng) && Number.isFinite(lastLat);
    map = new AMap.Map("map", {
      zoom: defaultZoom,
      mapStyle: mapStyle(),
      center: remembered ? [lastLng, lastLat] : DEFAULT_CENTER,
      resizeEnable: true,
      scrollWheel: true,
      dragEnable: true,
      zoomEnable: true,
    });
    stabilizeInitialView(remembered ? [lastLng, lastLat] : DEFAULT_CENTER);

    placeSearch = createPlaceSearch({ city: currentCityName, citylimit: false });

    if (remembered) {
      selectedMarker = updateMarker(selectedMarker, [lastLng, lastLat], "selected");
    }

    map.on("click", (event) => {
      const lng = event.lnglat.getLng();
      const lat = event.lnglat.getLat();
      const point = [lng, lat];
      selectedMarker = updateMarker(selectedMarker, point, "selected");
      if (bridge) {
        bridge.selectPoint(lng, lat);
      }
    });
    map.on("complete", refreshCurrentCity);
    map.on("moveend", refreshCurrentCity);

    bindControls();
    applyPendingMapActions();
    setStatus("");
  }

  function createPlaceSearch(options) {
    return new AMap.PlaceSearch({
      pageSize: 10,
      pageIndex: 1,
      city: options.city || "全国",
      citylimit: Boolean(options.citylimit),
    });
  }

  function refreshCurrentCity() {
    if (!map || typeof map.getCity !== "function") {
      return;
    }
    map.getCity((info) => {
      const city = info && (info.city || info.province);
      if (city) {
        currentCityName = city;
      }
    });
  }

  function stabilizeInitialView(center) {
    const refresh = () => {
      if (!map) {
        return;
      }
      map.resize();
      map.setZoomAndCenter(defaultZoom, center);
    };
    map.on("complete", function initialRefresh() {
      map.off("complete", initialRefresh);
      refresh();
    });
    setTimeout(refresh, 120);
    setTimeout(refresh, 600);
  }

  async function search(keyword) {
    if (!map || !placeSearch) {
      setStatus("地图尚未初始化完成。");
      return;
    }
    searchResults.innerHTML = '<div class="empty-result">搜索中...</div>';

    const city = (await getMapCity()) || currentCityName || "全国";
    const allPois = [];

    if (city && city !== "全国") {
      appendUniquePois(allPois, await searchByCity(keyword, city));
    }
    if (allPois.length < 10 && city && city !== "全国" && !keyword.includes(city.replace(/市$/, ""))) {
      appendUniquePois(allPois, await searchByCity(`${city}${keyword}`, city));
    }
    if (allPois.length < 10) {
      appendUniquePois(allPois, await searchByCity(keyword, "全国"));
    }
    if (allPois.length < 10) {
      appendUniquePois(allPois, await searchNearby(keyword));
    }

    if (!allPois.length) {
      renderResults([]);
      setStatus(`未找到地点：${keyword}`);
      return;
    }
    const pois = allPois.slice(0, 10);
    renderResults(pois);
    focusPoi(pois[0]);
    setStatus(`搜索结果：${pois.length} 条`);
  }

  function getMapCity() {
    return new Promise((resolve) => {
      if (!map || typeof map.getCity !== "function") {
        resolve(currentCityName);
        return;
      }
      map.getCity((info) => {
        const city = info && (info.city || info.province);
        if (city) {
          currentCityName = city;
          resolve(city);
        } else {
          resolve(currentCityName);
        }
      });
    });
  }

  function searchByCity(keyword, city) {
    return new Promise((resolve) => {
      const searcher = createPlaceSearch({ city, citylimit: false });
      searcher.search(keyword, (status, result) => {
        resolve(extractPois(status, result));
      });
    });
  }

  function searchNearby(keyword) {
    return new Promise((resolve) => {
      if (!map || !map.getCenter || !placeSearch.searchNearBy) {
        resolve([]);
        return;
      }
      const center = map.getCenter();
      placeSearch.searchNearBy(keyword, center, 80000, (status, result) => {
        resolve(extractPois(status, result));
      });
    });
  }

  function extractPois(status, result) {
    if (status !== "complete" || !result || !result.poiList || !result.poiList.pois) {
      return [];
    }
    return result.poiList.pois.filter((poi) => poi && poi.location);
  }

  function appendUniquePois(target, pois) {
    const seen = new Set(target.map((poi) => poiKey(poi)));
    pois.forEach((poi) => {
      const key = poiKey(poi);
      if (!seen.has(key)) {
        seen.add(key);
        target.push(poi);
      }
    });
  }

  function poiKey(poi) {
    if (poi.id) {
      return `id:${poi.id}`;
    }
    if (!poi.location) {
      return `name:${poi.name}`;
    }
    return [
      poi.name || "",
      poi.location.getLng().toFixed(6),
      poi.location.getLat().toFixed(6),
    ].join("|");
  }

  function renderResults(pois) {
    searchResults.innerHTML = "";
    if (!pois.length) {
      searchResults.innerHTML = '<div class="empty-result">未找到相关地点</div>';
      return;
    }
    pois.forEach((poi) => {
      const item = document.createElement("div");
      item.className = "result-item";
      const lng = poi.location.getLng();
      const lat = poi.location.getLat();
      const address = [poi.cityname, poi.adname, poi.address].filter(Boolean).join(" ");
      item.innerHTML = `
        <div class="result-name">${escapeHtml(poi.name || "未命名地点")}</div>
        <div class="result-address">${escapeHtml(address || "地址信息暂无")}</div>
        <div class="result-coord">${lng.toFixed(6)}, ${lat.toFixed(6)}</div>
      `;
      item.addEventListener("click", () => focusPoi(poi));
      searchResults.appendChild(item);
    });
  }

  function focusPoi(poi) {
    if (!poi || !poi.location) {
      return;
    }
    const point = [poi.location.getLng(), poi.location.getLat()];
    map.setZoomAndCenter(Math.max(defaultZoom, 16), point);
    searchMarker = updateMarker(searchMarker, point, "search");
    selectedMarker = updateMarker(selectedMarker, point, "selected");
    if (bridge) {
      bridge.selectPoint(point[0], point[1]);
    }
  }

  function bindControls() {
    searchButton.addEventListener("click", () => {
      const keyword = searchInput.value.trim();
      if (keyword) {
        setStatus(`搜索地点：${keyword}`);
        search(keyword);
      }
    });
    searchInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        searchButton.click();
      }
    });
    clearSearchButton.addEventListener("click", () => {
      searchInput.value = "";
      searchResults.innerHTML = "";
      searchInput.focus();
    });
    locateButton.addEventListener("click", () => {
      if (currentMarker) {
        map.setZoomAndCenter(defaultZoom, currentMarker.getPosition());
        return;
      }
      setStatus("正在请求当前位置...");
      if (bridge) {
        bridge.requestCurrentLocation();
      }
    });
  }

  function setCurrentLocation(longitude, latitude, recenter) {
    if (!window.AMap || !map) {
      pendingCurrentLocation = { longitude, latitude, recenter };
      return;
    }
    const point = [longitude, latitude];
    currentMarker = updateMarker(currentMarker, point, "current");
    if (recenter) {
      map.setZoomAndCenter(defaultZoom, point);
    }
    setTimeout(refreshCurrentCity, 80);
  }

  function showDefaultCenter() {
    if (!map) {
      pendingDefaultCenter = true;
      return;
    }
    map.setZoomAndCenter(defaultZoom, DEFAULT_CENTER);
    stabilizeInitialView(DEFAULT_CENTER);
  }

  function applyPendingMapActions() {
    if (pendingDefaultCenter) {
      pendingDefaultCenter = false;
      showDefaultCenter();
    }
    if (pendingCurrentLocation) {
      const location = pendingCurrentLocation;
      pendingCurrentLocation = null;
      setCurrentLocation(location.longitude, location.latitude, location.recenter);
    }
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    }[char]));
  }

  window.PinShiftMap = {
    setTheme,
    search,
    setCurrentLocation,
    showDefaultCenter,
  };

  async function bootstrap() {
    try {
      await initBridge();
      await loadAmap();
      initMap();
      setStatus("");
    } catch (error) {
      setStatus(error.message || "地图初始化失败。");
    }
  }

  bootstrap();
})();
