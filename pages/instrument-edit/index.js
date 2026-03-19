const { callService } = require('../../utils/api');

Page({
  data: {
    instrument: null,
    price: '',
    location: '',
    desc: ''
  },
  onLoad(options) {
    callService('getInstrumentEditDetail', { id: options.id }).then((res) => {
      this.setData({
        instrument: res.instrument,
        price: `${res.instrument.price}`,
        location: res.instrument.location,
        desc: res.instrument.desc
      });
    });
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  onInput(event) {
    this.setData({ [event.currentTarget.dataset.field]: event.detail.value });
  },
  submit() {
    callService('updateInstrument', {
      id: this.data.instrument.id,
      price: this.data.price,
      location: this.data.location,
      desc: this.data.desc
    }).then((res) => {
      wx.showModal({ title: '更新成功', content: res.message, showCancel: false });
    });
  }
});
