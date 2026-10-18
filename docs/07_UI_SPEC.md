# 07 — UI screens and interactions

## User journey (Vietnamese interface)

1. `/` — concise dashboard: demo badge, invoices, quick status statistics.
2. `/invoices/[id]` — fictional beneficiary, original CNY amount, due date and provenance.
3. `/checkout/[invoiceId]` — quote creation, demo FX conversion & fee breakdown with time-to-expiry, consent checkbox + clear CTA `Xác nhận thanh toán mô phỏng`.
4. `/payments/[id]` — processing animation/polling, status, ordered event timeline, safe failure message; staff-only demo provider scenario controls on a separate panel.
5. `/history` — past transactions and receipt access.
6. `/receipts/[id]` — printable simulation receipt, large watermark `DEMO - NOT AN ACTUAL PAYMENT`.
7. `/assistant` — P1 source-labelled policy/fee guidance. Never show as a required step for payment.

## Visual design

- Credible fintech layout, spacious cards, strong typographic hierarchy, helpful icons, consistent status badges.
- Clear title: `Thanh toán bảo hiểm du học – Bản mô phỏng`.
- Desktop navigation sidebar; mobile top navigation/stacked cards.
- No stock photos needed; polished data-centric UI using Tailwind/CSS.
- Dark mode optional; no need for expensive charts.
- Demo provenance and `Không chuyển tiền thật` shown on *every* payment-critical page and on receipt.
- Accessibility: keyboard operability, focus states, labels, `aria-live` for async updates, no color-only semantics.

## Exact quote preview seed case

```
Phí bảo hiểm:                   800.00 CNY
Tỷ giá thử nghiệm:              1 CNY = 3,500 VND
Quy đổi:                       2,800,000 VND
Phí xử lý thử nghiệm (1.5%):     42,000 VND
Phí cố định:                       5,000 VND
Tổng cộng:                     2,847,000 VND
[ ] Tôi hiểu đây là giao dịch giả lập.
[Xác nhận thanh toán mô phỏng]
```

## States and errors

`PENDING / PROCESSING / SUCCESS / FAILURE / CANCELLED / EXPIRED` all have plain-language descriptions. Clearly show exact retry behavior (create new quote/order) and never silently resubmit.
