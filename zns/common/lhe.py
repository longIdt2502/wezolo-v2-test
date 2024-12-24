

def generate_confirmation_order_pharmago(data):
    name = data.get("name", None)
    order_code = data.get("order_code")
    phone = data.get("phone")
    total_price = data.get("total_price")
    status = data.get("status")
    created_at = data.get("created_at")
    order_items = data.get("order_items")
    template = f"""Xác nhận đơn hàng
Cảm ơn {name} đã mua hàng tại cửa hàng. Đơn hàng của bạn đã được xác nhận với chi tiết như sau:

{4 * ' '}Mã đơn{13 * ' '}{order_code}
{4 * ' '}Điện thoại{9 * ' '}{phone}
{4 * ' '}Giá tiền{11 * ' '}{total_price} VNĐ
{4 * ' '}Trạng thái{9 * ' '}{status}
{4 * ' '}Ngày đặt hàng{6 * ' '}{created_at}
{4 * ' '}Sản phẩm{11 * ' '}{order_items}

Bạn vui lòng KIỂM TRA LẠI ĐƠN HÀNG."""
    return template


def generate_created_order_lhe(data):
    name = data.get("name", None)
    order_code = data.get("order_code")
    phone = data.get("phone_number")
    total_price = data.get("order_price")
    created_at = data.get("created_at")
    order_items = data.get("order_items")
    template = f"""Thông báo đặt hàng
Cảm ơn Quý khách hàng {name} đã đặt hàng. Đơn hàng của bạn đã được đặt với thông tin chi tiết sau:

{4 * ' '}Mã đơn{13 * ' '}{order_code}
{4 * ' '}Số điện thoại{6 * ' '}{phone}
{4 * ' '}Sản phẩm{11 * ' '}{order_items}
{4 * ' '}Giá tiền{11 * ' '}{total_price} VNĐ
{4 * ' '}Ngày đặt hàng{6 * ' '}{created_at}
Bạn vui lòng KIỂM TRA LẠI ĐƠN HÀNG."""
    return template


def generate_confirm_order_lhe(data):
    name = data.get("name", None)
    order_code = data.get("order_code")
    phone = data.get("phone_number")
    total_price = data.get("order_price")
    created_at = data.get("created_at")
    order_items = data.get("order_items")
    template = f"""Thông báo đặt hàng
Cảm ơn Quý khách hàng {name} đã đặt hàng. Đơn hàng của bạn đã được xác nhận với thông tin chi tiết sau:

{4 * ' '}Mã đơn{13 * ' '}{order_code}
{4 * ' '}Số điện thoại{6 * ' '}{phone}
{4 * ' '}Sản phẩm{11 * ' '}{order_items}
{4 * ' '}Giá tiền{11 * ' '}{total_price} VNĐ
{4 * ' '}Ngày đặt hàng{6 * ' '}{created_at}
"""
    return template
