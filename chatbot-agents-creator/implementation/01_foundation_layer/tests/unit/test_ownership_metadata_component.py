import unittest
from datetime import datetime
from src.architecture.ownership_metadata import OwnershipMetadata, OwnershipType


class TestOwnershipMetadataComponent(unittest.TestCase):
    """Test cases for the Ownership Metadata component"""

    def setUp(self):
        """Set up test environment"""
        self.ownership_manager = OwnershipMetadata()

    def test_validate_ownership(self):
        """Test ownership validation logic"""
        # System component (None owner_id) can be accessed by anyone
        self.assertTrue(self.ownership_manager.validate_ownership(None, "client1"))
        self.assertTrue(self.ownership_manager.validate_ownership(None, "client2"))
        
        # Client component can only be accessed by its owner
        self.assertTrue(self.ownership_manager.validate_ownership("client1", "client1"))
        self.assertFalse(self.ownership_manager.validate_ownership("client1", "client2"))
        self.assertFalse(self.ownership_manager.validate_ownership("client1", None))

    def test_transfer_ownership(self):
        """Test ownership transfer functionality"""
        # Create initial metadata
        metadata = {
            'owner_id': 'client1',
            'ownership_type': 'client',
            'exportable': True,
            'created_at': '2025-08-06T15:30:00Z'
        }
        
        # Transfer ownership from client1 to client2
        updated_metadata = self.ownership_manager.transfer_ownership('client1', 'client2', metadata)
        
        # Check updated metadata
        self.assertEqual(updated_metadata['owner_id'], 'client2')
        self.assertEqual(updated_metadata['previous_owner_id'], 'client1')
        self.assertTrue('ownership_transferred_at' in updated_metadata)
        
        # Attempt invalid transfer (wrong current owner)
        invalid_transfer = self.ownership_manager.transfer_ownership('client3', 'client2', metadata)
        self.assertEqual(invalid_transfer, metadata)  # Should return original metadata unchanged

    def test_create_ownership_metadata(self):
        """Test creation of ownership metadata"""
        # Create system ownership metadata
        system_metadata = self.ownership_manager.create_ownership_metadata()
        self.assertIsNone(system_metadata['owner_id'])
        self.assertEqual(system_metadata['ownership_type'], 'system')
        self.assertFalse(system_metadata['exportable'])
        
        # Create client ownership metadata
        client_metadata = self.ownership_manager.create_ownership_metadata(
            owner_id='client1',
            ownership_type=OwnershipType.CLIENT,
            exportable=True
        )
        self.assertEqual(client_metadata['owner_id'], 'client1')
        self.assertEqual(client_metadata['ownership_type'], 'client')
        self.assertTrue(client_metadata['exportable'])
        
        # Create shared ownership metadata
        shared_metadata = self.ownership_manager.create_ownership_metadata(
            owner_id='client1',
            ownership_type='shared',
            exportable=False
        )
        self.assertEqual(shared_metadata['owner_id'], 'client1')
        self.assertEqual(shared_metadata['ownership_type'], 'shared')
        self.assertFalse(shared_metadata['exportable'])
        
        # Test with invalid ownership type string
        invalid_type_metadata = self.ownership_manager.create_ownership_metadata(
            owner_id='client1',
            ownership_type='invalid_type'
        )
        self.assertEqual(invalid_type_metadata['ownership_type'], 'system')
        
        # Test client ownership without owner_id
        missing_owner_metadata = self.ownership_manager.create_ownership_metadata(
            ownership_type=OwnershipType.CLIENT
        )
        self.assertEqual(missing_owner_metadata['ownership_type'], 'system')

    def test_is_exportable(self):
        """Test exportable check functionality"""
        # Explicitly exportable
        metadata1 = {'exportable': True}
        self.assertTrue(self.ownership_manager.is_exportable(metadata1))
        
        # Client-owned (implicitly exportable)
        metadata2 = {'ownership_type': 'client', 'exportable': False}
        self.assertTrue(self.ownership_manager.is_exportable(metadata2))
        
        # Not exportable
        metadata3 = {'ownership_type': 'system', 'exportable': False}
        self.assertFalse(self.ownership_manager.is_exportable(metadata3))

    def test_get_ownership_summary(self):
        """Test ownership summary generation"""
        # Create test data
        components_by_owner = {
            None: ['system_component1', 'system_component2'],
            'client1': ['client1_component1', 'client1_component2', 'client1_component3'],
            'client2': ['client2_component1']
        }
        
        # Generate summary
        summary = self.ownership_manager.get_ownership_summary(components_by_owner)
        
        # Check summary data
        self.assertEqual(summary['total_components'], 6)
        self.assertEqual(summary['system_components'], 2)
        self.assertEqual(summary['client_components'], 4)
        self.assertEqual(summary['client_count'], 2)
        self.assertEqual(summary['components_by_owner']['system'], 2)
        self.assertEqual(summary['components_by_owner']['client1'], 3)
        self.assertEqual(summary['components_by_owner']['client2'], 1)


if __name__ == '__main__':
    unittest.main()