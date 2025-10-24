from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.tickets.models import Ticket, SavedFilter
from apps.companies.models import Company

User = get_user_model()


class TicketPaginationTestCase(TestCase):
    """Test cases for ticket list pagination"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create company
        self.company = Company.objects.create(
            name='Test Company',
            slug='test-company-pagination',
            email='test@company.com',
            phone_number='1234567890'
        )
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123',
            company=self.company,
            role='EMPLOYEE'
        )
        
        # Create multiple tickets for pagination testing
        self.tickets = []
        for i in range(25):  # Create 25 tickets (more than 1 page)
            ticket = Ticket.objects.create(
                reference=f'TKT-TEST{i:03d}',
                title=f'Test Ticket {i}',
                description=f'Test description for ticket {i}',
                status='OPEN' if i % 2 == 0 else 'IN_PROGRESS',
                priority='HIGH' if i % 3 == 0 else 'MEDIUM',
                company=self.company,
                created_by=self.user
            )
            self.tickets.append(ticket)
    
    def test_pagination_exists(self):
        """Test that pagination is present in ticket list"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('tickets:ticket_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['object_list']), 20)  # Default page size
    
    def test_pagination_second_page(self):
        """Test that second page shows remaining tickets"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('tickets:ticket_list') + '?page=2')
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['object_list']), 5)  # Remaining 5 tickets
    
    def test_pagination_with_filters(self):
        """Test that pagination works with filters applied"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('tickets:ticket_list') + '?status=OPEN')
        
        self.assertEqual(response.status_code, 200)
        # Should show only OPEN tickets
        for ticket in response.context['object_list']:
            self.assertEqual(ticket.status, 'OPEN')


class TicketFilterTestCase(TestCase):
    """Test cases for ticket filtering functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create company
        self.company = Company.objects.create(
            name='Test Company',
            slug='test-company-filter',
            email='test@company.com',
            phone_number='1234567890'
        )
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123',
            company=self.company,
            role='EMPLOYEE'
        )
        
        # Create tickets with different statuses and priorities
        self.ticket_open_high = Ticket.objects.create(
            reference='TKT-OPEN-HIGH',
            title='High Priority Open Ticket',
            description='This is a high priority open ticket',
            status='OPEN',
            priority='HIGH',
            company=self.company,
            created_by=self.user
        )
        
        self.ticket_open_medium = Ticket.objects.create(
            reference='TKT-OPEN-MED',
            title='Medium Priority Open Ticket',
            description='This is a medium priority open ticket',
            status='OPEN',
            priority='MEDIUM',
            company=self.company,
            created_by=self.user
        )
        
        self.ticket_progress_low = Ticket.objects.create(
            reference='TKT-PROG-LOW',
            title='Low Priority In Progress Ticket',
            description='This is a low priority in progress ticket',
            status='IN_PROGRESS',
            priority='LOW',
            company=self.company,
            created_by=self.user
        )
        
        self.ticket_resolved = Ticket.objects.create(
            reference='TKT-RESOLVED',
            title='Resolved Ticket',
            description='This is a resolved ticket',
            status='RESOLVED',
            priority='MEDIUM',
            company=self.company,
            created_by=self.user
        )
    
    def test_filter_by_status(self):
        """Test filtering tickets by status"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('tickets:ticket_list') + '?status=OPEN')
        
        self.assertEqual(response.status_code, 200)
        tickets = list(response.context['object_list'])
        self.assertEqual(len(tickets), 2)
        for ticket in tickets:
            self.assertEqual(ticket.status, 'OPEN')
    
    def test_filter_by_priority(self):
        """Test filtering tickets by priority"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('tickets:ticket_list') + '?priority=HIGH')
        
        self.assertEqual(response.status_code, 200)
        tickets = list(response.context['object_list'])
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0].priority, 'HIGH')
    
    def test_filter_by_multiple_statuses(self):
        """Test filtering tickets by multiple statuses"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('tickets:ticket_list') + '?status=OPEN&status=IN_PROGRESS'
        )
        
        self.assertEqual(response.status_code, 200)
        tickets = list(response.context['object_list'])
        self.assertEqual(len(tickets), 3)
        statuses = [t.status for t in tickets]
        self.assertIn('OPEN', statuses)
        self.assertIn('IN_PROGRESS', statuses)
    
    def test_filter_by_search(self):
        """Test filtering tickets by text search"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('tickets:ticket_list') + '?search=High+Priority')
        
        self.assertEqual(response.status_code, 200)
        tickets = list(response.context['object_list'])
        self.assertGreaterEqual(len(tickets), 1)
        # Verify that search found the high priority ticket
        ticket_titles = [t.title for t in tickets]
        self.assertIn('High Priority Open Ticket', ticket_titles)
    
    def test_filter_by_reference(self):
        """Test filtering tickets by reference number"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('tickets:ticket_list') + '?search=TKT-OPEN-HIGH')
        
        self.assertEqual(response.status_code, 200)
        tickets = list(response.context['object_list'])
        self.assertGreaterEqual(len(tickets), 1)
        self.assertEqual(tickets[0].reference, 'TKT-OPEN-HIGH')
    
    def test_combined_filters(self):
        """Test filtering tickets with multiple filter criteria"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('tickets:ticket_list') + '?status=OPEN&priority=HIGH'
        )
        
        self.assertEqual(response.status_code, 200)
        tickets = list(response.context['object_list'])
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0].reference, 'TKT-OPEN-HIGH')


class SavedFilterTestCase(TestCase):
    """Test cases for saved filter functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create company
        self.company = Company.objects.create(
            name='Test Company',
            slug='test-company-saved',
            email='test@company.com',
            phone_number='1234567890'
        )
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123',
            company=self.company,
            role='EMPLOYEE'
        )
    
    def test_save_filter(self):
        """Test saving a filter configuration"""
        self.client.login(username='testuser', password='testpass123')
        
        # Save the filter - POST data and GET params need to be combined
        # The view reads filter params from request.GET
        response = self.client.post(
            reverse('tickets:save_filter') + '?status=OPEN&priority=HIGH',
            {
                'filter_name': 'High Priority Open Tickets',
                'is_default': False
            }
        )
        
        # Check that filter was saved
        saved_filter = SavedFilter.objects.filter(
            user=self.user,
            name='High Priority Open Tickets'
        ).first()
        
        self.assertIsNotNone(saved_filter)
        self.assertEqual(saved_filter.name, 'High Priority Open Tickets')
        # Verify filter data was saved correctly
        filter_data = saved_filter.get_filter_params()
        self.assertEqual(filter_data.get('status'), 'OPEN')
        self.assertEqual(filter_data.get('priority'), 'HIGH')
    
    def test_load_saved_filter(self):
        """Test loading a saved filter"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create a saved filter
        saved_filter = SavedFilter.objects.create(
            user=self.user,
            name='Test Filter',
            filter_data={'status': 'OPEN', 'priority': 'HIGH'},
            is_default=False
        )
        
        # Load the filter
        response = self.client.get(
            reverse('tickets:load_filter', kwargs={'filter_id': saved_filter.id})
        )
        
        # Should redirect to ticket list with filter parameters
        self.assertEqual(response.status_code, 302)
    
    def test_delete_saved_filter(self):
        """Test deleting a saved filter"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create a saved filter
        saved_filter = SavedFilter.objects.create(
            user=self.user,
            name='Test Filter',
            filter_data={'status': 'OPEN'},
            is_default=False
        )
        
        # Delete the filter
        response = self.client.post(
            reverse('tickets:delete_filter', kwargs={'filter_id': saved_filter.id})
        )
        
        # Check that filter was deleted
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            SavedFilter.objects.filter(id=saved_filter.id).exists()
        )
    
    def test_clear_filters(self):
        """Test clearing all active filters"""
        self.client.login(username='testuser', password='testpass123')
        
        # Apply filters and then clear them
        response = self.client.get(reverse('tickets:clear_filters'))
        
        # Should redirect to ticket list without filters
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('tickets:ticket_list'), response.url)


class TicketListContextTestCase(TestCase):
    """Test cases for ticket list context data"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create company
        self.company = Company.objects.create(
            name='Test Company',
            slug='test-company-context',
            email='test@company.com',
            phone_number='1234567890'
        )
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123',
            company=self.company,
            role='EMPLOYEE'
        )
        
        # Create tickets with different statuses
        for status, _ in Ticket.STATUS:
            Ticket.objects.create(
                reference=f'TKT-{status}',
                title=f'Ticket {status}',
                description=f'Description for {status}',
                status=status,
                priority='MEDIUM',
                company=self.company,
                created_by=self.user
            )
    
    def test_statistics_in_context(self):
        """Test that ticket statistics are included in context"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('tickets:ticket_list'))
        
        self.assertEqual(response.status_code, 200)
        
        # Check that statistics are present
        self.assertIn('total_count', response.context)
        self.assertIn('open_count', response.context)
        self.assertIn('in_progress_count', response.context)
        self.assertIn('resolved_count', response.context)
        self.assertIn('closed_count', response.context)
        
        # Verify counts
        self.assertEqual(response.context['total_count'], 4)
        self.assertEqual(response.context['open_count'], 1)
        self.assertEqual(response.context['in_progress_count'], 1)
        self.assertEqual(response.context['resolved_count'], 1)
        self.assertEqual(response.context['closed_count'], 1)
