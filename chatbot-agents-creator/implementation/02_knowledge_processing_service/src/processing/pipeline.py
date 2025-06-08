from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable

class PipelineStage(ABC):
    """
    Abstract base class for pipeline stages.
    
    Each stage in the processing pipeline must implement this interface.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the pipeline stage.
        
        Args:
            config: Configuration dictionary for the stage
        """
        self.config = config or {}
        self.name = self.config.get('name', self.__class__.__name__)
        
    @abstractmethod
    def process(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a batch of items.
        
        Args:
            items: List of items to process
            
        Returns:
            Processed items
        """
        pass
        
    def validate(self) -> Dict[str, Any]:
        """
        Validate the stage configuration.
        
        Returns:
            Dictionary with validation results
        """
        return {
            'valid': True,
            'name': self.name,
            'type': self.__class__.__name__
        }


class Pipeline:
    """
    Processing pipeline for knowledge items.
    
    The pipeline consists of a series of stages that process items sequentially.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the pipeline.
        
        Args:
            config: Configuration dictionary for the pipeline
        """
        self.config = config or {}
        self.name = self.config.get('name', 'KnowledgeProcessingPipeline')
        self.stages = []
        self.hooks = {
            'before_pipeline': [],
            'after_pipeline': [],
            'before_stage': [],
            'after_stage': [],
            'on_error': []
        }
        
    def add_stage(self, stage: PipelineStage) -> 'Pipeline':
        """
        Add a stage to the pipeline.
        
        Args:
            stage: Pipeline stage to add
            
        Returns:
            Self for method chaining
        """
        self.stages.append(stage)
        return self
        
    def add_hook(self, hook_type: str, hook_func: Callable) -> 'Pipeline':
        """
        Add a hook function to the pipeline.
        
        Args:
            hook_type: Type of hook ('before_pipeline', 'after_pipeline', 
                      'before_stage', 'after_stage', 'on_error')
            hook_func: Hook function to call
            
        Returns:
            Self for method chaining
        """
        if hook_type in self.hooks:
            self.hooks[hook_type].append(hook_func)
        return self
        
    def process(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process items through the pipeline.
        
        Args:
            items: List of items to process
            
        Returns:
            Processed items
        """
        # Call before_pipeline hooks
        for hook in self.hooks['before_pipeline']:
            items = hook(items) or items
            
        current_items = items
        
        # Process each stage
        for stage in self.stages:
            try:
                # Call before_stage hooks
                for hook in self.hooks['before_stage']:
                    current_items = hook(current_items, stage) or current_items
                    
                # Process the stage
                current_items = stage.process(current_items)
                
                # Call after_stage hooks
                for hook in self.hooks['after_stage']:
                    current_items = hook(current_items, stage) or current_items
                    
            except Exception as e:
                # Call on_error hooks
                for hook in self.hooks['on_error']:
                    hook(e, current_items, stage)
                    
                # In a real implementation, this would log the error
                print(f"Error in pipeline stage {stage.name}: {str(e)}")
                
        # Call after_pipeline hooks
        for hook in self.hooks['after_pipeline']:
            current_items = hook(current_items) or current_items
            
        return current_items
        
    def validate(self) -> Dict[str, Any]:
        """
        Validate the pipeline configuration.
        
        Returns:
            Dictionary with validation results
        """
        result = {
            'valid': True,
            'name': self.name,
            'stages': [],
            'errors': [],
            'warnings': []
        }
        
        if not self.stages:
            result['warnings'].append('Pipeline has no stages')
            
        # Validate each stage
        for stage in self.stages:
            stage_result = stage.validate()
            result['stages'].append(stage_result)
            
            if not stage_result.get('valid', True):
                result['valid'] = False
                if 'errors' in stage_result:
                    result['errors'].extend([
                        f"{stage.name}: {error}" 
                        for error in stage_result['errors']
                    ])
                    
        return result