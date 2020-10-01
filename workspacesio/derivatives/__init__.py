"""
Derivatives are data objects deterministically generated from data managed in workspaces.
These could be thumbnails, transcoded media, etc.

The bytes live within the workspace, but they're costly enough to compute that it's worth
tracking them within the workspaces database.
"""
