#!/bin/bash
# Run LLD workflow for all issues without LLDs

ISSUES=(19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35)
TOTAL=${#ISSUES[@]}
COUNT=0

echo "=============================================="
echo "Running LLD workflow for $TOTAL issues"
echo "=============================================="
echo ""

for ISSUE in "${ISSUES[@]}"; do
    COUNT=$((COUNT + 1))
    echo ""
    echo "=============================================="
    echo "[$COUNT of $TOTAL] Processing Issue #$ISSUE"
    echo "=============================================="
    echo ""

    poetry run --directory /c/Users/mcwiz/Projects/AgentOS \
        python /c/Users/mcwiz/Projects/AgentOS/tools/run_requirements_workflow.py \
        --type lld \
        --issue "$ISSUE" \
        --gates none \
        --repo /c/Users/mcwiz/Projects/RCA-PDF-extraction-pipeline

    EXIT_CODE=$?

    if [ $EXIT_CODE -ne 0 ]; then
        echo ""
        echo "WARNING: Issue #$ISSUE failed with exit code $EXIT_CODE"
        echo "Continuing to next issue..."
    else
        echo ""
        echo "SUCCESS: Issue #$ISSUE LLD completed"
    fi

    echo ""
done

echo "=============================================="
echo "Complete: Processed $TOTAL issues"
echo "=============================================="
