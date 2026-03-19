const { invokeMockService } = require('./mock');

function getAppSafe() {
  try {
    return getApp();
  } catch (error) {
    return { globalData: { useCloud: false } };
  }
}

function callService(action, payload = {}) {
  const app = getAppSafe();
  const canUseCloud = app && app.globalData && app.globalData.useCloud && wx.cloud;

  if (!canUseCloud) {
    return Promise.resolve(invokeMockService(action, payload));
  }

  return wx.cloud
    .callFunction({
      name: 'gateway',
      data: {
        action,
        payload
      }
    })
    .then((res) => res.result)
    .catch((error) => {
      console.warn(`Cloud service failed for ${action}, using mock fallback.`, error);
      return invokeMockService(action, payload);
    });
}

module.exports = {
  callService
};
