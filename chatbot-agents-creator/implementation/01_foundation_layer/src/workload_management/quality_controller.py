class QualityController:
    """
    Ensures the quality of agent outputs through verification steps,
    feedback collection, and continuous improvement processes.
    """
    
    def __init__(self, config=None):
        self.config = config or {}
        self.quality_metrics = {}
        self.verification_steps = {}
        self.feedback_history = {}
        
    def register_quality_metric(self, metric_name, evaluation_function, threshold=0.7):
        """
        Register a quality metric for evaluating agent outputs
        
        Args:
            metric_name: Name of the quality metric
            evaluation_function: Function that evaluates an output and returns a score (0.0-1.0)
            threshold: Minimum acceptable score for this metric
        """
        self.quality_metrics[metric_name] = {
            'evaluation_function': evaluation_function,
            'threshold': threshold
        }
        
    def add_verification_step(self, task_type, verification_function):
        """
        Add a verification step for a specific task type
        
        Args:
            task_type: Type of task this verification applies to
            verification_function: Function that verifies the output
                                  Should return (passed, feedback)
        """
        if task_type not in self.verification_steps:
            self.verification_steps[task_type] = []
            
        self.verification_steps[task_type].append(verification_function)
        
    def evaluate_output(self, task_type, output, context=None):
        """
        Evaluate the quality of an agent's output
        
        Args:
            task_type: Type of task
            output: The output to evaluate
            context: Optional context information
            
        Returns:
            Dictionary with evaluation results
        """
        results = {
            'passed': True,
            'metrics': {},
            'verification': [],
            'overall_score': 0.0
        }
        
        # Apply quality metrics
        metric_scores = []
        for metric_name, metric_info in self.quality_metrics.items():
            try:
                score = metric_info['evaluation_function'](output, context)
                results['metrics'][metric_name] = {
                    'score': score,
                    'passed': score >= metric_info['threshold']
                }
                
                if score < metric_info['threshold']:
                    results['passed'] = False
                    
                metric_scores.append(score)
            except Exception as e:
                results['metrics'][metric_name] = {
                    'error': str(e),
                    'passed': False
                }
                results['passed'] = False
        
        # Calculate overall score
        if metric_scores:
            results['overall_score'] = sum(metric_scores) / len(metric_scores)
        
        # Run verification steps
        if task_type in self.verification_steps:
            for verification_function in self.verification_steps[task_type]:
                try:
                    step_passed, feedback = verification_function(output, context)
                    results['verification'].append({
                        'passed': step_passed,
                        'feedback': feedback
                    })
                    
                    if not step_passed:
                        results['passed'] = False
                except Exception as e:
                    results['verification'].append({
                        'error': str(e),
                        'passed': False
                    })
                    results['passed'] = False
        
        return results
        
    def record_feedback(self, task_id, agent_id, feedback_source, feedback_content, rating=None):
        """
        Record feedback for an agent's output
        
        Args:
            task_id: ID of the task
            agent_id: ID of the agent
            feedback_source: Source of the feedback (e.g., 'user', 'system')
            feedback_content: Content of the feedback
            rating: Optional numerical rating (e.g., 1-5)
        """
        if task_id not in self.feedback_history:
            self.feedback_history[task_id] = []
            
        self.feedback_history[task_id].append({
            'agent_id': agent_id,
            'source': feedback_source,
            'content': feedback_content,
            'rating': rating,
            'timestamp': None  # In a real implementation, this would be the current timestamp
        })
        
    def get_agent_feedback_history(self, agent_id):
        """
        Get the feedback history for a specific agent
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            List of feedback items for the agent
        """
        agent_feedback = []
        
        for task_id, feedback_list in self.feedback_history.items():
            for feedback in feedback_list:
                if feedback['agent_id'] == agent_id:
                    agent_feedback.append({
                        'task_id': task_id,
                        'feedback': feedback
                    })
                    
        return agent_feedback
        
    def get_improvement_suggestions(self, agent_id):
        """
        Generate improvement suggestions for an agent based on feedback history
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            List of improvement suggestions
        """
        # In a real implementation, this would analyze feedback patterns
        # and generate meaningful suggestions
        return []

    def route_task_to_best_agent(self, task_type, candidate_agents, context=None):
        """
        Route a task to the best agent based on historical quality scores.
        Args:
            task_type: The type of task to route
            candidate_agents: List of agent IDs to consider
            context: Optional context for routing
        Returns:
            agent_id: The best agent for the task, or None if no data
        """
        # Gather average quality scores for each agent
        agent_scores = {}
        for agent_id in candidate_agents:
            feedbacks = self.get_agent_feedback_history(agent_id)
            scores = []
            for fb in feedbacks:
                # Only consider feedback for this task type if available
                if fb['feedback'].get('task_type') == task_type or 'score' in fb['feedback']:
                    score = fb['feedback'].get('score')
                    if score is not None:
                        scores.append(score)
            if scores:
                agent_scores[agent_id] = sum(scores) / len(scores)
            else:
                agent_scores[agent_id] = 0.0  # Default if no feedback
        if not agent_scores:
            return None
        # Select agent with highest average score
        best_agent = max(agent_scores, key=agent_scores.get)
        return best_agent

    def apply_continuous_improvement(self, agent_id):
        """
        Apply continuous improvement processes for an agent based on feedback.
        Args:
            agent_id: The agent to improve
        """
        # Placeholder: In a real implementation, this could adjust thresholds,
        # retrain models, or trigger learning workflows based on feedback.
        pass

    def set_client_quality_standards(self, client_id, standards):
        """
        Set client-specific quality standards (thresholds, metrics).
        Args:
            client_id: The client ID
            standards: Dict of quality standards
        """
        if not hasattr(self, 'client_standards'):
            self.client_standards = {}
        self.client_standards[client_id] = standards

    def get_client_quality_standards(self, client_id):
        """
        Get client-specific quality standards.
        Args:
            client_id: The client ID
        Returns:
            Dict of quality standards, or None
        """
        if hasattr(self, 'client_standards'):
            return self.client_standards.get(client_id)
        return None

    def record_anonymized_feedback(self, task_id, feedback_content, rating=None):
        """
        Record anonymized feedback for a task (no agent or user ID).
        Args:
            task_id: ID of the task
            feedback_content: Content of the feedback
            rating: Optional numerical rating
        """
        if not hasattr(self, 'anonymized_feedback'):
            self.anonymized_feedback = {}
        if task_id not in self.anonymized_feedback:
            self.anonymized_feedback[task_id] = []
        self.anonymized_feedback[task_id].append({
            'content': feedback_content,
            'rating': rating,
            'timestamp': None  # In a real implementation, this would be the current timestamp
        })

    def generate_quality_metrics_dashboard(self, agent_id=None, client_id=None):
        """
        Generate a quality metrics dashboard for an agent or client.
        Args:
            agent_id: Optional agent ID to filter metrics
            client_id: Optional client ID to filter metrics
        Returns:
            Dict containing aggregated quality metrics and feedback data
        """
        dashboard = {
            'overall_score': 0.0,
            'metrics': {},
            'feedback_count': 0,
            'anonymized_feedback_count': 0
        }
        
        # Aggregate metrics
        for metric_name, metric_info in self.quality_metrics.items():
            scores = []
            for task_id, feedback_list in self.feedback_history.items():
                for feedback in feedback_list:
                    if agent_id and feedback['agent_id'] != agent_id:
                        continue
                    if client_id and feedback.get('client_id') != client_id:
                        continue
                    if 'score' in feedback:
                        scores.append(feedback['score'])
            if scores:
                dashboard['metrics'][metric_name] = sum(scores) / len(scores)
        
        # Count feedback
        for task_id, feedback_list in self.feedback_history.items():
            for feedback in feedback_list:
                if agent_id and feedback['agent_id'] != agent_id:
                    continue
                if client_id and feedback.get('client_id') != client_id:
                    continue
                dashboard['feedback_count'] += 1
        
        # Count anonymized feedback
        if hasattr(self, 'anonymized_feedback'):
            for task_id, feedback_list in self.anonymized_feedback.items():
                dashboard['anonymized_feedback_count'] += len(feedback_list)
        
        # Calculate overall score
        if dashboard['metrics']:
            dashboard['overall_score'] = sum(dashboard['metrics'].values()) / len(dashboard['metrics'])
        
        return dashboard