const { callService } = require('../../utils/api');

const REPORT_REASONS = [
  '参数与描述不一致，申请平台核验',
  '怀疑认证信息异常，申请复核资质',
  '交易条款表述不清，申请平台介入'
];

const VERIFIED_STATUSES = ['已认证', '已通过'];

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '操作失败，请稍后重试',
    icon: 'none'
  });
}

function normalizeInstrumentMedia(item = {}) {
  const images = Array.isArray(item.images) ? item.images.filter(Boolean) : [];
  return {
    ...item,
    images,
    coverImage: item.coverImage || images[0] || ''
  };
}

Page({
  data: {
    loading: true,
    instrument: null,
    isFavorite: false,
    recommendations: [],
    agreement: null,
    tradeMode: '',
    startDate: '',
    endDate: '',
    insuranceAccepted: false,
    insurancePlanId: '',
    insurancePlanNames: [],
    previewItem: null,
    previewTotal: 0,
    selectedInsuranceText: '请选择保单',
    canTrade: false,
    tradeBlockedMessage: ''
  },
  onLoad(options) {
    this.instrumentId = options.id;
    this.loadDetail(options.id);
  },
  loadDetail(id) {
    Promise.all([callService('getInstrumentDetail', { id }), callService('getProfile')])
      .then(([res, profile]) => {
        const instrument = normalizeInstrumentMedia({
          ...res.instrument,
          disciplinesText: (res.instrument.disciplines || []).join(' / ')
        });
        const dates = instrument.availableDates || [];
        const tradeMode =
          instrument.defaultTradeMode || (instrument.tradeModes && instrument.tradeModes[0]) || '租赁';
        const startDate = dates[0] || '';
        const endDate = dates[1] || dates[0] || '';
        const insurancePlanId =
          instrument.insurancePlans && instrument.insurancePlans[0]
            ? instrument.insurancePlans[0].id
            : '';
        const certification = (profile && profile.certification) || {};

        this.setData(
          {
            loading: false,
            instrument,
            isFavorite: res.isFavorite,
            recommendations: (res.recommendations || []).map(normalizeInstrumentMedia),
            agreement: res.agreement,
            tradeMode,
            startDate,
            endDate,
            insuranceAccepted: false,
            insurancePlanId,
            insurancePlanNames: (instrument.insurancePlans || []).map(
              (item) => `${item.name} · ¥${item.fee}`
            ),
            canTrade: VERIFIED_STATUSES.includes(certification.status),
            tradeBlockedMessage:
              certification.pendingMessage || '请先完成认证，再进入咨询、下单和购物车流程。'
          },
          () => this.refreshPreview()
        );
      })
      .catch(showError);
  },
  composePayload() {
    const { instrument, tradeMode, startDate, endDate, insurancePlanId, insuranceAccepted } = this.data;
    return {
      instrumentId: instrument.id,
      tradeMode,
      startDate,
      endDate,
      insurancePlanId,
      insuranceAccepted
    };
  },
  refreshPreview() {
    const { instrument } = this.data;
    if (!instrument) return;
    callService('getOrderPreview', this.composePayload())
      .then((preview) => {
        const previewItem = preview.selectedItem || preview.list[0] || null;
        this.setData({
          previewItem,
          previewTotal: preview.total || 0,
          selectedInsuranceText: previewItem
            ? `${previewItem.insurancePlan.name} · ${previewItem.insurancePlan.coverage}`
            : '请选择保单'
        });
      })
      .catch(() => {});
  },
  ensureTradeAccess() {
    if (this.data.canTrade) return true;
    wx.showModal({
      title: '请先完成认证',
      content: this.data.tradeBlockedMessage || '完成认证后才能联系发布方、加入购物车和下单。',
      confirmText: '去认证',
      success: ({ confirm }) => {
        if (confirm) {
          wx.navigateTo({ url: '/pages/certification/index' });
        }
      }
    });
    return false;
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  onTradeModeTap(event) {
    this.setData(
      {
        tradeMode: event.currentTarget.dataset.mode
      },
      () => this.refreshPreview()
    );
  },
  onStartDateChange(event) {
    const { instrument, endDate } = this.data;
    const startDate = instrument.availableDates[Number(event.detail.value)];
    this.setData(
      {
        startDate,
        endDate: new Date(endDate) < new Date(startDate) ? startDate : endDate
      },
      () => this.refreshPreview()
    );
  },
  onEndDateChange(event) {
    const { instrument, startDate } = this.data;
    const selected = instrument.availableDates[Number(event.detail.value)];
    this.setData(
      {
        endDate: new Date(selected) < new Date(startDate) ? startDate : selected
      },
      () => this.refreshPreview()
    );
  },
  onInsurancePlanChange(event) {
    const plan = this.data.instrument.insurancePlans[Number(event.detail.value)];
    this.setData(
      {
        insurancePlanId: plan.id
      },
      () => this.refreshPreview()
    );
  },
  toggleInsurance() {
    this.setData(
      {
        insuranceAccepted: !this.data.insuranceAccepted
      },
      () => this.refreshPreview()
    );
  },
  toggleFavorite() {
    callService('toggleFavorite', { instrumentId: this.data.instrument.id })
      .then((res) => {
        this.setData({ isFavorite: res.isFavorite });
        wx.showToast({ title: res.message, icon: 'none' });
      })
      .catch(showError);
  },
  addToCart() {
    if (!this.ensureTradeAccess()) return;
    callService('addToCart', this.composePayload())
      .then((res) => {
        wx.showToast({ title: res.message, icon: 'success' });
      })
      .catch(showError);
  },
  buyNow() {
    if (!this.ensureTradeAccess()) return;
    callService('addToCart', this.composePayload())
      .then(() => {
        wx.navigateTo({
          url: `/pages/order-confirm/index?instrumentId=${this.data.instrument.id}&tradeMode=${encodeURIComponent(this.data.tradeMode)}`
        });
      })
      .catch(showError);
  },
  goChat() {
    if (!this.ensureTradeAccess()) return;
    callService('ensureInstrumentChat', {
      instrumentId: this.data.instrument.id
    })
      .then((res) => {
        wx.navigateTo({ url: `/pages/chat-detail/index?id=${res.chatId}` });
      })
      .catch(showError);
  },
  goAgreement() {
    wx.navigateTo({
      url: `/pages/agreement/index?instrumentId=${this.data.instrument.id}`
    });
  },
  reportInstrument() {
    wx.showActionSheet({
      itemList: REPORT_REASONS,
      success: ({ tapIndex }) => {
        callService('submitReport', {
          targetType: '仪器',
          targetName: this.data.instrument.name,
          reason: REPORT_REASONS[tapIndex]
        })
          .then((res) => {
            wx.showToast({ title: res.message, icon: 'none' });
          })
          .catch(showError);
      }
    });
  },
  openInstrument(event) {
    wx.redirectTo({
      url: `/pages/equipment-detail/index?id=${event.currentTarget.dataset.id}`
    });
  }
});
