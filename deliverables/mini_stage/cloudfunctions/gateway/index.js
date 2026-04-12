const cloud = require('wx-server-sdk');

cloud.init({
  env: cloud.DYNAMIC_CURRENT_ENV
});

const { invokeCloudService } = require('./cloud-db');

exports.main = async (event) => {
  const { action, payload = {} } = event;
  const wxContext = cloud.getWXContext();

  try {
    return await invokeCloudService(action, payload, wxContext);
  } catch (error) {
    console.warn(`Cloud service failed for ${action}.`, error);
    return {
      success: false,
      message: error.message || 'Service failed'
    };
  }
};
