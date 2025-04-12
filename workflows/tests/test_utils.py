# workflows/tests/test_utils.py
from django.test import TestCase
from workflows.utils import execute_node
from workflows.models import Workflow, Node
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

User = get_user_model()

class ExecuteNodeTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='utilstestuser',
            email='utils@example.com',
            password='utilspass123'
        )
        
        cls.workflow = Workflow.objects.create(
            name="Utils Test Workflow",
            user=cls.user,
            config={'continue_on_error': True}
        )
        
        cls.text_input_node = Node.objects.create(
            workflow=cls.workflow,
            type="text_input",
            config={},
            order=1
        )
        
        cls.tts_node = Node.objects.create(
            workflow=cls.workflow,
            type="openai_tts",
            config={'voice': 'echo'},
            order=2
        )
        
        cls.summarization_node = Node.objects.create(
            workflow=cls.workflow,
            type="huggingface_summarization",
            config={},
            order=3
        )
    
    def test_text_input_node(self):
        """Test execution of text_input node"""
        input_data = "This is a test input"
        result = execute_node(self.text_input_node, input_data)
        self.assertEqual(result, input_data)
    
    @patch('workflows.utils.gTTS')
    def test_tts_node(self, mock_gtts):
        """Test execution of openai_tts node"""
        mock_tts_instance = MagicMock()
        mock_gtts.return_value = mock_tts_instance
        
        input_data = "Convert this text to speech"
        result = execute_node(self.tts_node, input_data)
        
        # Check that gTTS was called correctly
        mock_gtts.assert_called_once_with(text=input_data, lang='en')
        mock_tts_instance.write_to_fp.assert_called_once()
        self.assertEqual(result, "TTS audio generated successfully")
    
    @patch('workflows.utils.summarizer_pipeline')
    def test_summarization_node(self, mock_summarizer):
        """Test execution of huggingface_summarization node"""
        mock_summarizer.return_value = [{'summary_text': 'This is a summary'}]
        
        input_data = "This is a long text that needs to be summarized. " * 10
        result = execute_node(self.summarization_node, input_data)
        
        mock_summarizer.assert_called_once_with(input_data)
        self.assertEqual(result, "This is a summary")
    
    def test_unknown_node_type(self):
        """Test execution of unknown node type"""
        unknown_node = Node.objects.create(
            workflow=self.workflow,
            type="unknown_type",
            config={},
            order=4
        )
        
        with self.assertRaises(ValueError):
            execute_node(unknown_node, "test input")
    
    def test_continue_on_error(self):
        """Test continue_on_error functionality"""
        unknown_node = Node.objects.create(
            workflow=self.workflow,
            type="unknown_type",
            config={},
            order=4
        )
        
        # With continue_on_error=True, should return error message instead of raising
        result = execute_node(unknown_node, "test input", continue_on_error=True)
        self.assertTrue(result.startswith("ERROR"))
        self.assertIn("Unknown node type", result)