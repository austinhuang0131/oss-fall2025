# Chat Ticket Integration

Integration layer that connects chat APIs with ticket APIs to enable command-based ticket management through chat messages.

## Overview

This package provides a bridge between chat systems and ticket systems, allowing users to manage tickets through chat commands.

## Architecture

- Accepts any chat API implementation and any ticket API implementation via dependency injection
- Polls chat messages at regular intervals
- Parses commands from messages
- Executes corresponding ticket operations
