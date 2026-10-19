function formatTimestamp(date) {
  const pad = (value) => String(value).padStart(2, "0");

  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} `
    + `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}

export function log(
  messages,
  message,
  messageType = "info",
  newLine = true,
  date = new Date(),
) {
  const timestamp = formatTimestamp(date);
  const type = ["info", "warning", "error"].includes(messageType) ? messageType : "info";
  const lines = message.split(/\r\n|\r|\n/);
  const next = [...messages];

  if (!newLine && next.length > 0 && !next[next.length - 1].separator) {
    const last = next.length - 1;
    next[last] = { ...next[last], message: next[last].message + lines.shift() };
  }

  return next.concat(lines.map((line) => ({ timestamp, messageType: type, message: line })));
}
