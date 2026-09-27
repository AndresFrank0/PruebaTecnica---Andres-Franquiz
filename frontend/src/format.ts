// Formato es-VE, con el mismo criterio que formatBs/formatRate de ACuanto.
const money = new Intl.NumberFormat("es-VE", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const rate = new Intl.NumberFormat("es-VE", { maximumFractionDigits: 4 });

export const formatUsd = (value: number) => `$${money.format(value)}`;
export const formatBs = (value: number) => `Bs. ${money.format(value)}`;
export const formatRate = (value: number) => rate.format(value);
