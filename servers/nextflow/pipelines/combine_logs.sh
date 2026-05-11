#!/usr/bin/env bash
# collect_nf_logs.sh
# Concatenates .command.out logs from all tasks in a Nextflow run into a
# single file with clear section headers.
#
# Usage:
#   ./collect_nf_logs.sh [work_dir] [output_file]
#
# Defaults:
#   work_dir    = ./work
#   output_file = ./nf_logs_combined.txt

set -euo pipefail

WORK_DIR="${1:-./work}"
OUTPUT_FILE="${2:-./nf_logs_combined.txt}"

if [[ ! -d "$WORK_DIR" ]]; then
  echo "ERROR: work directory not found: $WORK_DIR" >&2
  exit 1
fi

# Resolve to absolute path for cleaner display
WORK_DIR="$(cd "$WORK_DIR" && pwd)"

echo "Collecting logs from : $WORK_DIR"
echo "Writing output to    : $OUTPUT_FILE"

# ── helpers ────────────────────────────────────────────────────────────────

# Extract the task name Nextflow stores inside .command.run, e.g.:
#   nxf_task_name='ALIGN_READS (sample1)'
get_task_name() {
  local run_file="$1/.command.run"
  if [[ -f "$run_file" ]]; then
    # Try both single-quoted and double-quoted variants
    grep -m1 "nxf_task_name=" "$run_file" \
      | sed "s/.*nxf_task_name=['\"]//; s/['\"].*$//" \
      2>/dev/null || true
  fi
}

# ── main ───────────────────────────────────────────────────────────────────

# Collect all .command.out paths, sorted for reproducible order
mapfile -t LOG_FILES < <(
  find "$WORK_DIR" -name ".command.out" | sort
)

TOTAL="${#LOG_FILES[@]}"

if [[ "$TOTAL" -eq 0 ]]; then
  echo "No .command.out files found under $WORK_DIR."
  exit 0
fi

echo "Found $TOTAL task log(s)."

# Write header banner
{
  echo "############################################################"
  echo "  Nextflow combined task logs"
  printf "  Generated : %s\n" "$(date '+%Y-%m-%d %H:%M:%S')"
  printf "  Work dir  : %s\n" "$WORK_DIR"
  printf "  Tasks     : %d\n" "$TOTAL"
  echo "############################################################"
  echo ""
} > "$OUTPUT_FILE"

COUNT=0
for LOG in "${LOG_FILES[@]}"; do
  COUNT=$(( COUNT + 1 ))
  TASK_DIR="$(dirname "$LOG")"

  # Relative path from work dir (e.g. ab/cdef1234...)
  REL_PATH="${TASK_DIR#"$WORK_DIR"/}"

  # Friendly task name from .command.run, fall back to relative path
  TASK_NAME="$(get_task_name "$TASK_DIR")"
  if [[ -z "$TASK_NAME" ]]; then
    TASK_NAME="$REL_PATH"
  fi

  {
    echo "============================================================"
    printf "  Task %d / %d\n" "$COUNT" "$TOTAL"
    printf "  Name : %s\n" "$TASK_NAME"
    printf "  Path : %s\n" "$REL_PATH"
    echo "============================================================"

    if [[ -s "$LOG" ]]; then
      cat "$LOG"
    else
      echo "(empty)"
    fi

    echo ""
  } >> "$OUTPUT_FILE"
done

echo "Done. Combined log written to: $OUTPUT_FILE"