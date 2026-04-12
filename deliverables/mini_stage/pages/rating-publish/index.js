const { callService } = require('../../utils/api');

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '提交失败，请稍后重试',
    icon: 'none'
  });
}

Page({
  data: {
    orderId: '',
    target: '',
    score: '5',
    content: ''
  },
  onLoad(options) {
    this.setData({
      orderId: options.orderId || '',
      target: options.target ? decodeURIComponent(options.target) : ''
    });
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  onInput(event) {
    this.setData({ [event.currentTarget.dataset.field]: event.detail.value });
  },
  submit() {
    if (!this.data.target.trim() || !this.data.content.trim()) {
      wx.showToast({ title: '请填写评价对象和内容', icon: 'none' });
      return;
    }
    const score = Number(this.data.score);
    if (!score || score < 1 || score > 5) {
      wx.showToast({ title: '评分需在 1-5 分之间', icon: 'none' });
      return;
    }
    callService('publishRating', this.data)
      .then((res) => {
        wx.showModal({ title: '提交成功', content: res.message, showCancel: false });
      })
      .catch(showError);
  }
});
