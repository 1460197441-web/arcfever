const { callService } = require('../../utils/api');

function createTradeModeOptions(selected = ['租赁']) {
  return ['租赁', '出售'].map((value) => ({
    value,
    selected: selected.includes(value)
  }));
}

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '更新失败，请稍后重试',
    icon: 'none'
  });
}

Page({
  data: {
    instrument: null,
    tradeModeOptions: createTradeModeOptions(),
    form: {
      price: '',
      salePrice: '',
      deposit: '',
      location: '',
      precision: '',
      disciplines: '',
      servicePackage: '',
      desc: '',
      breachRulesText: '',
      damageRulesText: '',
      remote: false,
      withDataPackage: false
    }
  },
  onLoad(options) {
    callService('getInstrumentEditDetail', { id: options.id })
      .then((res) => {
        const instrument = res.instrument;
        this.setData({
          instrument,
          tradeModeOptions: createTradeModeOptions(instrument.tradeModes || ['租赁']),
          form: {
            price: `${instrument.price || ''}`,
            salePrice: `${instrument.salePrice || ''}`,
            deposit: `${instrument.deposit || ''}`,
            location: instrument.location || '',
            precision: instrument.precision || '',
            disciplines: (instrument.disciplines || []).join('、'),
            servicePackage: instrument.servicePackage || '',
            desc: instrument.desc || '',
            breachRulesText: (instrument.breachRules || []).join('\n'),
            damageRulesText: (instrument.damageRules || []).join('\n'),
            remote: !!instrument.remote,
            withDataPackage: !!instrument.withDataPackage
          }
        });
      })
      .catch(showError);
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  onInput(event) {
    this.setData({ [`form.${event.currentTarget.dataset.field}`]: event.detail.value });
  },
  toggleTradeMode(event) {
    const mode = event.currentTarget.dataset.mode;
    const selectedModes = this.data.tradeModeOptions
      .filter((item) => item.selected)
      .map((item) => item.value);

    let nextModes = selectedModes.includes(mode)
      ? selectedModes.filter((item) => item !== mode)
      : selectedModes.concat(mode);

    if (!nextModes.length) {
      nextModes = [mode];
    }

    this.setData({
      tradeModeOptions: createTradeModeOptions(nextModes)
    });
  },
  toggleFlag(event) {
    const field = event.currentTarget.dataset.field;
    this.setData({ [`form.${field}`]: !this.data.form[field] });
  },
  submit() {
    const tradeModes = this.data.tradeModeOptions.filter((item) => item.selected).map((item) => item.value);
    callService('updateInstrument', {
      id: this.data.instrument.id,
      ...this.data.form,
      tradeModes,
      defaultTradeMode: tradeModes[0]
    })
      .then((res) => {
        wx.showModal({ title: '更新成功', content: res.message, showCancel: false });
      })
      .catch(showError);
  }
});
