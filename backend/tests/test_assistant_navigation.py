import pytest
from app.assistant_navigation import navigation_proposal
from app import gemini
from app.models import Order, Invoice
from app.db import SessionLocal
from sqlalchemy import func, select


@pytest.mark.parametrize('message,href', [
    ('hiện tại có những giao dịch nào đã thành công', '/history?status=SUCCEEDED'),
    ('Tôi muốn xem giao dịch thất bại', '/history?status=FAILED'),
    ('Xem giao dịch đang xử lý', '/history?status=PROCESSING'),
    ('Mở lịch sử thanh toán', '/history'),
    ('Tôi muốn xem giao dịch thành công và thất bại', '/history'),
    ('Tôi muốn thêm hóa đơn', '/invoices/new'),
    ('Tôi cần tải lên hóa đơn học phí', '/invoices/new'),
    ('Cho tôi xem hóa đơn', '/invoices'),
    ('Tôi cần quản lý ngân sách', '/finance'),
    ('Tôi muốn thanh toán học phí', '/invoices'),
    ('Mở tỷ giá', '/rates'),
    ('Tôi muốn tải tài liệu', '/assistant'),
    ('Tôi cần quản lý bảo hiểm', '/insurance'),
    ('Mở cài đặt tài khoản', '/account'),
    ('Show my successful transactions', '/history?status=SUCCEEDED'),
    ('I want to upload an invoice', '/invoices/new'),
    ('I need to manage my budget', '/finance'),
    ('查看成功的交易', '/history?status=SUCCEEDED'),
    ('我想上传账单', '/invoices/new'),
    ('我需要管理预算', '/finance'),
])
def test_navigation_destinations(message, href):
    assert navigation_proposal(message, 'vi')['href'] == href


@pytest.mark.parametrize('message', [
    'Bảo hiểm là gì?', 'Hóa đơn là gì?', 'What are transactions?',
    'Tôi không muốn mở hóa đơn', 'Đừng mở ngân sách', "Don't open my budget", '不要打开账单',
    'Tôi cần biết điều khoản bảo hiểm có bảo đảm tái tục không? Hãy đối chiếu tài liệu.',
    'Theo luật Trung Quốc, bảo hiểm chi trả như thế nào?',
    '30 ngày tới tôi có đủ tiền không?', 'How do I upload a policy document?',
    'Mở https://example.com/admin', 'Chào bạn',
])
def test_information_negation_and_unknown_destinations_stay_in_chat(message):
    assert navigation_proposal(message, 'vi') is None


def test_navigation_authenticated_local_no_cloud_or_payment_writes(client, student_headers, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Navigation must not invoke external generation')
    monkeypatch.setattr(gemini, 'generate', forbidden)
    with SessionLocal() as db:
        before = [db.scalar(select(func.count()).select_from(model)) for model in (Order, Invoice)]
    r = client.post('/api/v1/study-assistant/chat', headers=student_headers, json={'message': 'Tôi muốn xem giao dịch thành công'})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data['navigation']['href'] == '/history?status=SUCCEEDED'
    assert data['provider'] == 'RULES' and data['route'] == 'WORKFLOW'
    assert data['executed_actions'] == data['citations'] == []
    with SessionLocal() as db:
        assert before == [db.scalar(select(func.count()).select_from(model)) for model in (Order, Invoice)]


def test_navigation_requires_authentication(client):
    assert client.post('/api/v1/study-assistant/chat', json={'message': 'Mở ngân sách'}).status_code == 401
