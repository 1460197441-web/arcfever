const envConfig = require('./utils/env');

App({
  globalData: {
    useCloud: envConfig.useCloud !== false,
    cloudEnvId: envConfig.cloudEnvId || ''
  },
  onLaunch() {
    if (!wx.cloud) {
      this.globalData.useCloud = false;
      return;
    }

    try {
      const initOptions = {
        traceUser: true
      };

      if (envConfig.cloudEnvId) {
        initOptions.env = envConfig.cloudEnvId;
      }

      wx.cloud.init(initOptions);
    } catch (error) {
      this.globalData.useCloud = false;
      console.warn('Cloud init failed, falling back to mock services.', error);
    }
  }
});
