const { callService } = require('../../utils/api');

Page({
  data: {
    target: '',
    score: '5',
    content: ''
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  onInput(event) {
    this.setData({ [event.currentTarget.dataset.field]: event.detail.value });
  },
  submit() {
    callService('publishRating', this.data).then((res) => {
      wx.showModal({ title: '提交成功', content: res.message, showCancel: false });
    });
  }
});
