const { callService } = require('../../utils/api');

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '加载失败，请稍后重试',
    icon: 'none'
  });
}

Page({
  data: {
    agreement: null,
    instrument: null
  },
  onLoad(options) {
    const tasks = [callService('getAgreementContent')];
    if (options.instrumentId) {
      tasks.push(callService('getInstrumentDetail', { id: options.instrumentId }));
    }
    Promise.all(tasks)
      .then(([agreement, instrumentDetail]) => {
        this.setData({
          agreement,
          instrument: instrumentDetail ? instrumentDetail.instrument : null
        });
      })
      .catch(showError);
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  }
});
