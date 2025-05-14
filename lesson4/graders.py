bug_feature_grader = {
    "name": "Bug vs Feature Match",
    "type": "string_check",                  # built-in template
    "input": "{{sample.choices[0].message.content}}",       # agent's output to check
    "operation": "eq",                       # exact equality comparison
    "reference": "{{item.label}}",           # expected label to compare against
}



feature_quality_grader = {
    "name": "Feature proposal rubric",
    "type": "label_model",         # model-graded criterion
    "model": "o3",        # use a **different / stronger** model than your agent
    "input": [
        {
            "role": "developer",
            "content": (
                "You are a senior PM. Evaluate the draft below.\n"
                "Pass if ALL are true:\n"
                "1. Addresses the user's request accurately.\n"
                "2. Mentions at least one relevant competitor.\n"
                "3. Contains a clear benefit statement and implementation outline.\n"
                "Answer with: PASS or FAIL."
            ),
        },
        {
            "role": "user",
            "content": (
                "User review: {{item.review}}\n\n"
                "Draft proposal:\n{{sample.choices[0].message.content}}"
            ),
        },
    ],
    "passing_labels": ["PASS"],
    "labels": ["PASS", "FAIL"],
}

