App({
  globalData: {
    useCloud: true
  },
  onLaunch() {
    if (!wx.cloud) {
      this.globalData.useCloud = false;
      return;
    }

    try {
      wx.cloud.init({
        traceUser: true
      });
    } catch (error) {
      this.globalData.useCloud = false;
      console.warn('Cloud init failed, falling back to mock services.', error);
    }
  }
});
