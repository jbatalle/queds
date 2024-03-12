export function toCurrency(value, currency, digits = 2) {
  if (typeof value !== "number") {
    return value;
  }
  if (currency === undefined) {
    return Number(value).toFixed(digits);
  }
  try {
    let formatter = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      maximumFractionDigits: digits
    });
    return formatter.format(value);
  }
  catch(err) {
    console.log("Error formatting currency: " + currency + ": " + err);
    let formatter = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: "BTC",
      maximumFractionDigits: digits
    });
    return formatter.format(value).replace("BTC", currency);
  }
}

export function round(value) {
  if (typeof value !== "number") {
    return value;
  }
  return Number(value).toFixed(2);
}