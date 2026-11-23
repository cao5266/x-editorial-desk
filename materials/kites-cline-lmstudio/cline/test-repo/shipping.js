function shippingFee(subtotal, member = false) {
  if (!Number.isFinite(subtotal) || subtotal < 0) {
    throw new RangeError('subtotal must be a non-negative finite number');
  }
  return member || subtotal >= 100 ? 0 : 12;
}

module.exports = { shippingFee };
