#!/bin/bash
# Сумісність зі старим сценарієм: усе робить ctf.sh
cd "$(dirname "$0")"
exec bash ./ctf.sh setup
