"""
Plotting style definitions and utilities for publication-quality figures.

This module provides a configurable styling system for Plotly figures through
the Styler class, with support for both light and dark themes.

Example:
    # Basic usage
    styler = Styler()
    styler.apply_style(fig)

    # Dark mode
    styler = Styler(dark_mode=True)
    styler.apply_style(fig)

    # Custom parameters
    styler = Styler(title_size=24, grid_color="#FF0000")
    styler.apply_style(fig)

    # Dark mode with custom parameters
    styler = Styler(dark_mode=True, title_size=28)
    styler.apply_style(fig)
"""

from dataclasses import dataclass
from typing import Any

import plotly.graph_objects as go


@dataclass
class StyleConfig:
    """Configuration object for figure styling parameters.

    This dataclass contains all customizable styling parameters for publication-quality
    figures. Users can create custom configurations or modify existing ones.
    """

    # Font settings
    font_family: str = "Helvetica"
    font_color: str = "#333333"
    title_color: str = "#333333"  # Separate color for titles

    # Font sizes
    title_size: int = 20
    axis_title_size: int = 16
    tick_label_size: int = 16
    subtitle_size: int = 11
    legend_size: int = 12
    subplot_title_size: int = 14

    # Axis styling
    show_grid: bool = True
    grid_width: int = 1
    grid_color: str = "#E7E7E7"
    show_zeroline: bool = False
    line_width: int = 2
    line_color: str = "#333333"

    # Layout colors
    plot_background: str = "#FBFCFF"
    paper_background: str = "#FBFCFF"

    # Theme template (for dark mode)
    template: str | None = None


@dataclass
class ColorscaleConfig:
    """Configuration for colorscale generation with optional zero color override."""

    name: str
    zero_color: str | None = None


class Styler:
    """Main styling class that combines configuration data with styling behavior.

    This class provides a clean interface for applying consistent styling to Plotly figures.
    Users can customize styling parameters during instantiation, toggle dark mode, or modify
    the configuration after creation.

    Example:
        # Light mode with defaults
        styler = Styler()
        styler.apply_style(fig)

        # Dark mode
        styler = Styler(dark_mode=True)
        styler.apply_style(fig)

        # Custom styling
        styler = Styler(title_size=24, grid_color="#0000FF")
        styler.apply_style(fig)

        # Dark mode with custom styling
        styler = Styler(dark_mode=True, title_size=28, grid_color="#444444")
        styler.apply_style(fig)
    """

    def __init__(self, dark_mode: bool = False, **kwargs: Any) -> None:
        """Initialize styler with configuration parameters.

        Args:
            dark_mode: Whether to use dark theme defaults
            **kwargs: Any StyleConfig parameter to override default values
        """
        self.dark_mode = dark_mode

        # Apply dark mode defaults if requested
        if dark_mode:
            dark_defaults = {
                "font_color": "#DFDFDF",
                "title_color": "#DFDFDF",
                "grid_color": "#444444",
                "line_color": "#868686",
                "plot_background": "black",
                "paper_background": "black",
                "template": "plotly_dark",
            }
            # User kwargs override dark defaults
            dark_defaults.update(kwargs)
            self.config = StyleConfig(**dark_defaults)  # type:ignore
        else:
            self.config = StyleConfig(**kwargs)  # type:ignore

        self._font_cache: dict[tuple[int, bool, bool], dict[str, Any]] = {}
        self._axis_style_cache: dict[str, Any] | None = None

    def _get_font_dict(self, size: int, bold: bool = False, for_title: bool = False) -> dict[str, Any]:
        """Create consistent font dictionaries with caching.

        Args:
            size: Font size to use
            bold: Whether to use bold font weight
            for_title: Whether this font is for a title (uses title_color)

        Returns:
            Dictionary with font settings
        """
        cache_key = (size, bold, for_title)
        if cache_key not in self._font_cache:
            font_color = self.config.title_color if for_title else self.config.font_color
            self._font_cache[cache_key] = {
                "family": self.config.font_family,
                "size": size,
                "color": font_color,
                "weight": "bold" if bold else None,
            }
        return self._font_cache[cache_key]

    def _get_axis_style_dict(self) -> dict[str, Any]:
        """Generate axis style dictionary from configuration with caching.

        Returns:
            Dictionary with axis styling parameters
        """
        if self._axis_style_cache is None:
            self._axis_style_cache = {
                "showgrid": self.config.show_grid,
                "gridwidth": self.config.grid_width,
                "gridcolor": self.config.grid_color,
                "zeroline": self.config.show_zeroline,
                "linewidth": self.config.line_width,
                "linecolor": self.config.line_color,
            }
        return self._axis_style_cache

    def _invalidate_cache(self) -> None:
        """Invalidate internal caches when configuration changes."""
        self._font_cache.clear()
        self._axis_style_cache = None

    def _update_axis(self, axis: go.layout.XAxis | go.layout.YAxis) -> None:
        """Update a single axis with styling from configuration.

        Args:
            axis: Axis object to update
        """
        axis_style = self._get_axis_style_dict()
        axis.update(
            axis_style,
            title_font=self._get_font_dict(self.config.axis_title_size, bold=True),
            tickfont=self._get_font_dict(self.config.tick_label_size),
        )

    def apply_fonts(self, fig: go.Figure) -> None:
        """Apply publication-quality font settings to a figure.

        Args:
            fig: A plotly figure
        """
        # Update global font
        fig.update_layout(font=self._get_font_dict(self.config.tick_label_size))

        # Update title font if title exists
        if fig.layout.title is not None:
            fig.layout.title.update(font=self._get_font_dict(self.config.title_size, bold=True, for_title=True))

        # Update subplot titles if they exist
        if fig.layout.annotations:
            for annotation in fig.layout.annotations:
                if "<b>" in str(annotation.text):  # This is a subplot title
                    annotation.update(
                        font=self._get_font_dict(self.config.subplot_title_size, bold=True, for_title=True)
                    )

    def apply_axis_style(self, fig: go.Figure, row: int | None = None, col: int | None = None, **kwargs: Any) -> None:
        """Apply specific styling to one or more axes of a Plotly figure.

        This method allows fine-grained control over axis styling:
        - If `row` (1-indexed) is provided, it styles the corresponding x-axis
        - If `col` (1-indexed) is provided, it styles the corresponding y-axis
        - If both are provided, both the specified x-axis and y-axis are styled
        - If neither is provided, it styles the default axes

        Args:
            fig: A Plotly figure object
            row: Optional 1-indexed number for the x-axis to style
            col: Optional 1-indexed number for the y-axis to style
            **kwargs: Axis style parameters to override configuration defaults
        """
        # Get base axis style and apply overrides
        axis_style = self._get_axis_style_dict().copy()
        axis_style.update(kwargs)

        styled_specific_axis = False

        if row is not None:
            x_axis_name = f"xaxis{row if row > 1 else ''}"
            if hasattr(fig.layout, x_axis_name):
                axis_obj = getattr(fig.layout, x_axis_name)
                if axis_obj is not None:
                    axis_obj.update(
                        axis_style,
                        title_font=self._get_font_dict(self.config.axis_title_size, bold=True),
                        tickfont=self._get_font_dict(self.config.tick_label_size),
                    )
                    styled_specific_axis = True

        if col is not None:
            y_axis_name = f"yaxis{col if col > 1 else ''}"
            if hasattr(fig.layout, y_axis_name):
                axis_obj = getattr(fig.layout, y_axis_name)
                if axis_obj is not None:
                    axis_obj.update(
                        axis_style,
                        title_font=self._get_font_dict(self.config.axis_title_size, bold=True),
                        tickfont=self._get_font_dict(self.config.tick_label_size),
                    )
                    styled_specific_axis = True

        # Style default axes if no specific row/col was provided or found
        if not styled_specific_axis and row is None and col is None:
            for axis_obj in [fig.layout.xaxis, fig.layout.yaxis]:
                if axis_obj is not None:
                    axis_obj.update(
                        axis_style,
                        title_font=self._get_font_dict(self.config.axis_title_size, bold=True),
                        tickfont=self._get_font_dict(self.config.tick_label_size),
                    )

    def apply_style(self, fig: go.Figure, **kwargs: Any) -> None:
        """Apply all publication-quality styling to a figure.

        Args:
            fig: A plotly figure
            **kwargs: Additional layout parameters to override configuration defaults
        """
        # Apply fonts
        self.apply_fonts(fig)

        # Apply axis styling to all axes
        for key in fig.layout:
            if key.startswith("xaxis") or key.startswith("yaxis"):
                axis_obj = getattr(fig.layout, key)
                if axis_obj is not None:
                    self._update_axis(axis_obj)

        # Prepare layout style from configuration
        layout_style = {
            "plot_bgcolor": self.config.plot_background,
            "paper_bgcolor": self.config.paper_background,
        }

        if self.config.template is not None:
            layout_style["template"] = self.config.template

        # Override with any user-provided kwargs
        layout_style.update(kwargs)

        # Update layout with styling and legend
        fig.update_layout(layout_style, legend={"font": self._get_font_dict(self.config.legend_size)})

    def update_config(self, **kwargs: Any) -> None:
        """Update configuration parameters and invalidate caches.

        Args:
            **kwargs: StyleConfig parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                raise AttributeError(f"StyleConfig has no attribute '{key}'")

        self._invalidate_cache()

    def toggle_dark_mode(self) -> None:
        """Toggle between light and dark mode, updating configuration accordingly."""
        self.dark_mode = not self.dark_mode

        if self.dark_mode:
            # Switch to dark mode defaults
            self.config.font_color = "#DFDFDF"
            self.config.title_color = "#DFDFDF"
            self.config.grid_color = "#444444"
            self.config.line_color = "#868686"
            self.config.plot_background = "black"
            self.config.paper_background = "black"
            self.config.template = "plotly_dark"
        else:
            # Switch to light mode defaults
            self.config.font_color = "#333333"
            self.config.title_color = "#333333"
            self.config.grid_color = "#E7E7E7"
            self.config.line_color = "#333333"
            self.config.plot_background = "#FBFCFF"
            self.config.paper_background = "#FBFCFF"
            self.config.template = None

        self._invalidate_cache()

    def copy(self, **kwargs: Any) -> "Styler":
        """Create a copy of this styler with optional parameter overrides.

        Args:
            **kwargs: StyleConfig parameters to override in the copy

        Returns:
            New Styler instance with modified configuration
        """
        # Create dict from current config
        config_dict = {
            field.name: getattr(self.config, field.name) for field in self.config.__dataclass_fields__.values()
        }

        # Apply overrides
        config_dict.update(kwargs)

        return Styler(dark_mode=self.dark_mode, **config_dict)
