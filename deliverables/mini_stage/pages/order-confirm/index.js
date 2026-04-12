const { callService } = require('../../utils/api');

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '操作失败，请稍后重试',
    icon: 'none'
  });
}

Page({
  data: {
    loading: true,
    preview: null,
    instrument: null,
    selectedItem: null,
    insurancePlanNames: [],
    selectedInsuranceText: '',
    tradeMode: '',
    startDate: '',
    endDate: '',
    insurancePlanId: '',
    insuranceAccepted: false,
    agreementAccepted: false,
    damageAccepted: false,
    remark: ''
  },
  onLoad(options) {
    this.instrumentId = options.instrumentId || '';
    this.initialTradeMode = options.tradeMode ? decodeURIComponent(options.tradeMode) : '';
    this.loadPreview();
  },
  loadPreview() {
    const payload = this.instrumentId
      ? {
          instrumentId: this.instrumentId,
          tradeMode: this.data.tradeMode || this.initialTradeMode,
          startDate: this.data.startDate,
          endDate: this.data.endDate,
          insurancePlanId: this.data.insurancePlanId,
          insuranceAccepted: this.data.insuranceAccepted
        }
      : {};

    callService('getOrderPreview', payload)
      .then((preview) => {
        const selectedItem = preview.selectedItem || preview.list[0] || null;
        const instrument = selectedItem ? selectedItem.instrument : preview.selectedInstrument;
        if (instrument) {
          this.instrumentId = instrument.id;
        }
        this.setData({
          loading: false,
          preview,
          instrument: instrument || null,
          selectedItem,
          insurancePlanNames: instrument
            ? (instrument.insurancePlans || []).map((item) => `${item.name} · ¥${item.fee}`)
            : [],
          selectedInsuranceText: selectedItem
            ? `${selectedItem.insurancePlan.name} · ${selectedItem.insurancePlan.coverage}`
            : '',
          tradeMode: selectedItem ? selectedItem.tradeMode : this.data.tradeMode || this.initialTradeMode,
          startDate: selectedItem ? selectedItem.startDate : '',
          endDate: selectedItem ? selectedItem.endDate : '',
          insurancePlanId: selectedItem ? selectedItem.insurancePlan.id : '',
          insuranceAccepted: selectedItem ? !!selectedItem.insuranceAccepted : false
        });
      })
      .catch(showError);
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  onTradeModeTap(event) {
    this.setData(
      {
        tradeMode: event.currentTarget.dataset.mode
      },
      () => this.loadPreview()
    );
  },
  onStartDateChange(event) {
    const instrument = this.data.instrument;
    if (!instrument) return;
    const startDate = instrument.availableDates[Number(event.detail.value)];
    this.setData(
      {
        startDate,
        endDate: new Date(this.data.endDate) < new Date(startDate) ? startDate : this.data.endDate
      },
      () => this.loadPreview()
    );
  },
  onEndDateChange(event) {
    const instrument = this.data.instrument;
    if (!instrument) return;
    const endDate = instrument.availableDates[Number(event.detail.value)];
    this.setData(
      {
        endDate: new Date(endDate) < new Date(this.data.startDate) ? this.data.startDate : endDate
      },
      () => this.loadPreview()
    );
  },
  onInsurancePlanChange(event) {
    const plan = this.data.instrument.insurancePlans[Number(event.detail.value)];
    this.setData(
      {
        insurancePlanId: plan.id
      },
      () => this.loadPreview()
    );
  },
  toggleInsurance() {
    this.setData(
      {
        insuranceAccepted: !this.data.insuranceAccepted
      },
      () => this.loadPreview()
    );
  },
  toggleAgreement() {
    this.setData({ agreementAccepted: !this.data.agreementAccepted });
  },
  toggleDamage() {
    this.setData({ damageAccepted: !this.data.damageAccepted });
  },
  onInput(event) {
    this.setData({ remark: event.detail.value });
  },
  goAgreement() {
    wx.navigateTo({
      url: `/pages/agreement/index?instrumentId=${this.instrumentId}`
    });
  },
  submitOrder() {
    const { instrument, tradeMode, startDate, endDate, insurancePlanId, insuranceAccepted, remark } =
      this.data;
    if (!instrument) {
      wx.showToast({ title: '当前没有可提交的仪器', icon: 'none' });
      return;
    }

    callService('createOrder', {
      instrumentId: instrument.id,
      tradeMode,
      startDate,
      endDate,
      insurancePlanId,
      insuranceAccepted,
      agreementAccepted: this.data.agreementAccepted,
      damageAccepted: this.data.damageAccepted,
      remark
    })
      .then((res) => {
        wx.navigateTo({
          url: `/pages/order-payment/index?orderId=${res.orderId}`
        });
      })
      .catch(showError);
  }
});
