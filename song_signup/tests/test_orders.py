from django.test import TestCase
from django.db.utils import IntegrityError
from unittest.mock import patch
from song_signup.models import TicketOrder
from song_signup.views import _process_orders

from unittest.mock import MagicMock


@patch('song_signup.views.load_workbook')
class TestProcessOrders(TestCase):
    @staticmethod
    def setup_mock_data(mock_load_workbook, data):
        mock_worksheet = MagicMock()
        mock_worksheet.iter_rows.return_value = data
        mock_workbook = MagicMock()
        mock_workbook.active = mock_worksheet
        mock_load_workbook.return_value = mock_workbook

    def assert_db_data(self, expected_data):
        db_data = list(TicketOrder.objects.all().order_by('order_id').values_list(
            'order_id', 'event_sku', 'event_name', 'num_tickets', 'ticket_type', 'customer_name'
        ))

        self.assertEqual(len(db_data), len(expected_data), "Number of records mismatch")
        self.assertSetEqual(set(db_data), set(expected_data))

    def test_clean_db(self, mock_load_workbook):
        new_excel_data = [
            (5015162, 'GOGB5TT9CX', 'Event3', 4, 'ATTN', 'לקוח', 'חוזר'),
            (5015162, 'GOGB5TT9CX', 'Event3', 3, 'SING', 'לקוח', 'חוזר'),
            (5015155, 'GOGB5TT9CX', 'Event3', 4, 'ATTN', 'לקוח', 'חדש'),
            (5015154, 'GOGB5TT9CX', 'Event3', 1, 'SING', 'אדם', 'חדש'),
            (5015153, 'DIFFSKU001', 'Event4', 1, 'ATTN', 'מישהו', 'אחר'),
            (5015153, 'DIFFSKU001', 'Event4', 1, 'SING', 'מישהו', 'אחר'),
            (5015150, 'DIFFSKU001', 'Event4', 1, 'SING', 'אלון', 'אביב'),
            (5015150, 'DIFFSKU001', 'Event4', 3, 'ATTN', 'אלון', 'אביב'),
            (5015148, 'DIFFSKU001', 'Event4', 2, 'ATTN', 'אלון', 'אביב'),
        ]

        expected_db_data = [
            (5015162, 'GOGB5TT9CX', 'Event3', 4, 'ATTN', 'לקוח חוזר'),
            (5015162, 'GOGB5TT9CX', 'Event3', 3, 'SING', 'לקוח חוזר'),
            (5015155, 'GOGB5TT9CX', 'Event3', 4, 'ATTN', 'לקוח חדש'),
            (5015154, 'GOGB5TT9CX', 'Event3', 1, 'SING', 'אדם חדש'),
            (5015153, 'DIFFSKU001', 'Event4', 1, 'ATTN', 'מישהו אחר'),
            (5015153, 'DIFFSKU001', 'Event4', 1, 'SING', 'מישהו אחר'),
            (5015150, 'DIFFSKU001', 'Event4', 1, 'SING', 'אלון אביב'),
            (5015150, 'DIFFSKU001', 'Event4', 3, 'ATTN', 'אלון אביב'),
            (5015148, 'DIFFSKU001', 'Event4', 2, 'ATTN', 'אלון אביב'),
        ]

        self.setup_mock_data(mock_load_workbook, new_excel_data)
        result = _process_orders('dummy/path/to/file.xlsx')

        self.assertEqual(result['num_orders'], 6)
        self.assertEqual(result['num_ticket_orders'], 9)
        self.assertEqual(result['num_new_ticket_orders'], 9)
        self.assertEqual(result['num_existing_ticket_orders'], 0)
        self.assertEqual(result['num_singing_tickets'], 6)
        self.assertEqual(result['num_audience_tickets'], 14)

        self.assert_db_data(expected_db_data)

    def test_existing_data(self, mock_load_workbook):
        TicketOrder.objects.bulk_create([
            TicketOrder(order_id=5015162, event_sku='GOGB5TT9CX', event_name='Event3', num_tickets=4, ticket_type='ATTN', customer_name='לקוח חוזר'),
            TicketOrder(order_id=5015162, event_sku='GOGB5TT9CX', event_name='Event3', num_tickets=2, ticket_type='SING', customer_name='לקוח חוזר'),
            TicketOrder(order_id=5015200, event_sku='DIFFSKU002', event_name='Event5', num_tickets=2, ticket_type='ATTN', customer_name='מישהו אחר'),
            TicketOrder(order_id=5015200, event_sku='DIFFSKU002', event_name='Event5', num_tickets=3, ticket_type='SING', customer_name='מישהו אחר'),
            TicketOrder(order_id=5015300, event_sku='DIFFSKU003', event_name='Event6', num_tickets=3, ticket_type='SING', customer_name='אדם אחר')
        ])

        new_excel_data = [
            (5015162, 'GOGB5TT9CX', 'Event3', 4, 'ATTN', 'לקוח', 'חוזר'),  # Existing
            (5015162, 'GOGB5TT9CX', 'Event3', 2, 'SING', 'לקוח', 'חוזר'),  # Existing
            (5015155, 'GOGB5TT9CX', 'Event3', 4, 'ATTN', 'לקוח', 'חדש'),  # New
            (5015154, 'GOGB5TT9CX', 'Event3', 1, 'SING', 'אדם', 'חדש')  # New
        ]

        expected_db_data = [
            (5015162, 'GOGB5TT9CX', 'Event3', 4, 'ATTN', 'לקוח חוזר'),
            (5015162, 'GOGB5TT9CX', 'Event3', 2, 'SING', 'לקוח חוזר'),
            (5015155, 'GOGB5TT9CX', 'Event3', 4, 'ATTN', 'לקוח חדש'),
            (5015154, 'GOGB5TT9CX', 'Event3', 1, 'SING', 'אדם חדש'),
            (5015200, 'DIFFSKU002', 'Event5', 2, 'ATTN', 'מישהו אחר'),
            (5015200, 'DIFFSKU002', 'Event5', 3, 'SING', 'מישהו אחר'),
            (5015300, 'DIFFSKU003', 'Event6', 3, 'SING', 'אדם אחר')
        ]

        self.setup_mock_data(mock_load_workbook, new_excel_data)
        result = _process_orders('dummy/path/to/file.xlsx')

        self.assertEqual(result['num_orders'], 3)
        self.assertEqual(result['num_ticket_orders'], 4)
        self.assertEqual(result['num_new_ticket_orders'], 2)
        self.assertEqual(result['num_existing_ticket_orders'], 2)
        self.assertEqual(result['num_singing_tickets'], 3)
        self.assertEqual(result['num_audience_tickets'], 8)

        self.assert_db_data(expected_db_data)

    def test_override_orders(self, mock_load_workbook):
        TicketOrder.objects.bulk_create([
            TicketOrder(order_id=5015162, event_sku='GOGB5TT9CX', event_name='Event3', num_tickets=4, ticket_type='ATTN', customer_name='Original Name 1'),
            TicketOrder(order_id=5015154, event_sku='GOGB5TT9CX', event_name='Event3', num_tickets=1, ticket_type='SING', customer_name='Original Name 2')
        ])

        new_excel_data = [
            (5015162, 'GOGB5TT9CX', 'Event3', 3, 'ATTN', 'לקוח', 'חוזר'),
            (5015154, 'GOGB5TT9CX', 'Event3', 2, 'SING', 'אדם', 'חדש')
        ]

        expected_db_data = [
            (5015162, 'GOGB5TT9CX', 'Event3', 3, 'ATTN', 'לקוח חוזר'),
            (5015154, 'GOGB5TT9CX', 'Event3', 2, 'SING', 'אדם חדש')
        ]

        self.setup_mock_data(mock_load_workbook, new_excel_data)
        with self.assertRaises(IntegrityError):
            _process_orders('dummy/path/to/file.xlsx')


    def test_atomicity(self, mock_load_workbook):
        TicketOrder.objects.bulk_create([
            TicketOrder(order_id=5015162, event_sku='GOGB5TT9CX', event_name='Event3', num_tickets=4, ticket_type='ATTN', customer_name='שם קיים 1'),
            TicketOrder(order_id=5015154, event_sku='GOGB5TT9CX', event_name='Event3', num_tickets=1, ticket_type='SING', customer_name='שם קיים 2')
        ])

        new_excel_data = [
            (5015200, 'DIFFSKU001', 'Event4', 3, 'ATTN', 'חדש', 'אדם'), # Valid
            (5015162, 'GOGB5TT9CX', 'Event3', 3, 'ATTN', 'לקוח', 'חוזר'), # Invalid - Duplicate unique keys
            (5015201, 'DIFFSKU002', 'Event5', 2, 'SING', 'אחר', 'אדם'), # Valid
            (5015154, 'GOGB5TT9CX', 'Event3', 2, 'SING', 'אדם', 'חדש')  # Invalid - Duplicate unique keys
        ]

        self.setup_mock_data(mock_load_workbook, new_excel_data)
        with self.assertRaises(IntegrityError):
            _process_orders('dummy/path/to/file.xlsx')

        # Verify that the database state is unchanged
        existing_db_data = [
            (5015162, 'GOGB5TT9CX', 'Event3', 4, 'ATTN', 'שם קיים 1'),
            (5015154, 'GOGB5TT9CX', 'Event3', 1, 'SING', 'שם קיים 2')
        ]
        self.assert_db_data(existing_db_data)
