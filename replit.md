# Overview

A YouTube API service built with Flask that provides video downloading, searching, and conversion capabilities using yt-dlp and ffmpeg. The application offers RESTful endpoints for interacting with YouTube content, including downloading videos in various formats, extracting metadata, and retrieving thumbnails.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Framework
- **Flask** - Lightweight Python web framework chosen for rapid development and simplicity
- **RESTful API design** - Clean endpoint structure for video operations
- **Modular function design** - Separate utility functions for video ID extraction, filename cleaning, and file handling

## Video Processing Pipeline
- **yt-dlp** - Primary library for YouTube video extraction and metadata retrieval
- **ffmpeg** - Video/audio processing and format conversion capabilities
- **Temporary file management** - Dedicated temp and download directories for file operations

## File Management System
- **Download directory structure** - Organized storage for processed videos
- **Secure filename handling** - Input sanitization using werkzeug's secure_filename
- **Temporary file cleanup** - Structured approach to managing temporary files during processing

## API Design Patterns
- **JSON responses** - Consistent API response format
- **Error handling** - Structured error responses for various failure scenarios
- **URL parsing utilities** - Support for multiple YouTube URL formats (youtube.com and youtu.be)

## Configuration Management
- **Environment-based secrets** - Session key configuration through environment variables
- **Fallback configurations** - Default values for missing environment variables

# External Dependencies

## Core Libraries
- **yt-dlp** - YouTube video downloading and metadata extraction
- **ffmpeg-python** - Video/audio processing and format conversion
- **Flask** - Web framework and HTTP server
- **requests** - HTTP client for external API calls

## System Dependencies
- **ffmpeg** - Required system binary for video processing operations

## File System
- **Local storage** - Downloads and temporary files stored on local filesystem
- **Directory management** - Automatic creation of required directories

## YouTube Integration
- **YouTube platform** - Direct integration through yt-dlp for video access
- **Multiple URL format support** - Handles various YouTube URL structures
- **Metadata extraction** - Video information, thumbnails, and format details