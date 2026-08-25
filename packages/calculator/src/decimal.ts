import Decimal from 'decimal.js';

Decimal.set({
  precision: 40,
  rounding: Decimal.ROUND_HALF_EVEN,
  toExpNeg: -100,
  toExpPos: 100
});

export { Decimal };

export function dec(value: Decimal.Value | null | undefined): Decimal {
  if (value === null || value === undefined || value === '') return new Decimal(0);
  return new Decimal(String(value).replaceAll(',', '').trim());
}

export function decimalString(value: Decimal.Value): string {
  const result = dec(value);
  return result.isZero() ? '0' : result.toFixed();
}

export function percent(value: Decimal.Value): Decimal {
  return dec(value).div(100);
}

export function sum(values: Iterable<Decimal.Value>): Decimal {
  let result = new Decimal(0);
  for (const value of values) result = result.plus(value);
  return result;
}

export function product(values: Iterable<Decimal.Value>): Decimal {
  let result = new Decimal(1);
  for (const value of values) result = result.times(value);
  return result;
}
