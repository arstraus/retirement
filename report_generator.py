"""
PDF Report Generator for Retirement Forecasts
Creates professional, comprehensive PDF reports with charts and data.
"""

import io
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfgen import canvas
import plotly.graph_objects as go
from PIL import Image as PILImage


class RetirementReportGenerator:
    """Generate professional PDF reports for retirement forecasts."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom paragraph styles for the report."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#374151'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=10,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        ))
        
        # Body text with better spacing
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            fontName='Helvetica'
        ))
    
    def generate_report(
        self,
        scenario_name: str,
        people: List[Dict[str, Any]],
        financial: Dict[str, Any],
        investment: Dict[str, Any],
        taxes: Dict[str, Any],
        social_security: Dict[str, Any],
        forecast_years: int,
        summary: Dict[str, Any],
        forecast_df: pd.DataFrame
    ) -> bytes:
        """
        Generate a comprehensive PDF report.
        
        Args:
            scenario_name: Name of the scenario
            people: List of person dictionaries
            financial: Financial parameters
            investment: Investment parameters
            taxes: Tax parameters
            social_security: Social Security parameters
            forecast_years: Number of years forecasted
            summary: Summary metrics dictionary
            forecast_df: Forecast DataFrame
            
        Returns:
            PDF file as bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Title Page
        elements.extend(self._create_title_page(scenario_name))
        elements.append(PageBreak())
        
        # Executive Summary
        elements.extend(self._create_executive_summary(summary, forecast_df))
        elements.append(PageBreak())
        
        # Scenario Inputs
        elements.extend(self._create_inputs_section(
            people, financial, investment, taxes, social_security, forecast_years
        ))
        elements.append(PageBreak())
        
        # Detailed Analysis
        elements.extend(self._create_analysis_section(summary, forecast_df))
        
        # Charts Section
        elements.append(PageBreak())
        elements.extend(self._create_charts_section(forecast_df))
        
        # Year-by-Year Data (comprehensive table)
        elements.append(PageBreak())
        elements.extend(self._create_comprehensive_data_table(forecast_df))
        
        # Build PDF
        doc.build(elements)
        
        # Get the value of the BytesIO buffer and return it
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def _create_title_page(self, scenario_name: str) -> List:
        """Create the title page."""
        elements = []
        
        # Add vertical space
        elements.append(Spacer(1, 2*inch))
        
        # Title
        title = Paragraph("Retirement Wealth Forecast", self.styles['CustomTitle'])
        elements.append(title)
        elements.append(Spacer(1, 0.3*inch))
        
        # Scenario name
        scenario = Paragraph(f"<b>{scenario_name}</b>", self.styles['CustomSubtitle'])
        elements.append(scenario)
        elements.append(Spacer(1, 0.5*inch))
        
        # Date
        date_str = datetime.now().strftime("%B %d, %Y")
        date_para = Paragraph(f"Generated: {date_str}", self.styles['CustomBody'])
        elements.append(date_para)
        
        return elements
    
    def _create_executive_summary(self, summary: Dict[str, Any], forecast_df: pd.DataFrame) -> List:
        """Create executive summary section."""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.styles['CustomTitle']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Key metrics in a table
        data = [
            ['Metric', 'Value'],
            ['Assets at Retirement', self._format_currency(summary.get('retirement_assets', 0))],
            ['Peak Assets', self._format_currency(summary['peak_assets'])],
            ['Peak Year', str(int(summary['peak_year']))],
            ['Final Assets', self._format_currency(summary['final_assets'])],
            ['Final Age', str(int(summary['final_age']))],
            ['Total Taxes Paid', self._format_currency(summary['total_taxes_paid'])],
            ['Assets Status', 'Sustainable' if not summary.get('assets_depleted') else f"Depleted by year {int(summary.get('depletion_year', 0))}"]
        ]
        
        table = Table(data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Status message
        if summary.get('assets_depleted'):
            status = f"<font color='red'><b>Warning:</b> Assets are projected to be depleted by year {int(summary['depletion_year'])}.</font>"
        else:
            status = "<font color='green'><b>Good News:</b> Assets are projected to last through the forecast period.</font>"
        
        elements.append(Paragraph(status, self.styles['CustomBody']))
        
        return elements
    
    def _create_inputs_section(
        self,
        people: List[Dict[str, Any]],
        financial: Dict[str, Any],
        investment: Dict[str, Any],
        taxes: Dict[str, Any],
        social_security: Dict[str, Any],
        forecast_years: int
    ) -> List:
        """Create scenario inputs section."""
        elements = []
        
        elements.append(Paragraph("Scenario Inputs", self.styles['CustomTitle']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Household section
        elements.append(Paragraph("Household", self.styles['SectionHeader']))
        for i, person in enumerate(people):
            person_info = f"""
            <b>Person {i+1}: {person['name']}</b><br/>
            Age: {person['age']} | Retirement Age: {person['retirement_age']}<br/>
            Annual Cash Salary: {self._format_currency(person['current_income'])}<br/>
            Annual RSU Vesting: {self._format_currency(person.get('annual_rsu_vesting', 0))}<br/>
            Income Growth Rate: {person['income_growth_rate']*100:.1f}%<br/>
            Retirement Income: {self._format_currency(person['retirement_income'])}
            """
            elements.append(Paragraph(person_info, self.styles['CustomBody']))
            elements.append(Spacer(1, 0.1*inch))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Financial section
        elements.append(Paragraph("Financial", self.styles['SectionHeader']))
        fin_info = f"""
        Initial Assets: {self._format_currency(financial['initial_assets'])}<br/>
        Annual Expenses: {self._format_currency(financial['annual_expenses'])}<br/>
        Expense Growth Rate: {financial['expense_growth_rate']*100:.1f}%<br/>
        Additional Annual Savings: {self._format_currency(financial['additional_contributions'])}
        """
        elements.append(Paragraph(fin_info, self.styles['CustomBody']))
        
        # Account breakdown if available
        if financial.get('account_balances'):
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph("<b>Account Breakdown:</b>", self.styles['CustomBody']))
            balances = financial['account_balances']
            account_info = f"""
            Traditional 401k: {self._format_currency(balances.get('traditional_401k', 0))}<br/>
            Traditional IRA: {self._format_currency(balances.get('traditional_ira', 0))}<br/>
            Roth 401k: {self._format_currency(balances.get('roth_401k', 0))}<br/>
            Roth IRA: {self._format_currency(balances.get('roth_ira', 0))}<br/>
            Taxable Brokerage: {self._format_currency(balances.get('taxable', 0))}<br/>
            HSA: {self._format_currency(balances.get('hsa', 0))}
            """
            elements.append(Paragraph(account_info, self.styles['CustomBody']))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Investment section
        elements.append(Paragraph("Investment Assumptions", self.styles['SectionHeader']))
        inv_info = f"""
        Expected Annual Return: {investment['investment_return_rate']*100:.1f}%<br/>
        Inflation Rate: {investment['inflation_rate']*100:.1f}%
        """
        elements.append(Paragraph(inv_info, self.styles['CustomBody']))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Tax & Social Security
        elements.append(Paragraph("Taxes & Benefits", self.styles['SectionHeader']))
        tax_info = f"""
        State: {taxes['state']}<br/>
        Social Security Starting Age: {social_security['age']}<br/>
        Annual Social Security Benefit: {self._format_currency(social_security['benefit'])}<br/>
        Forecast Period: {forecast_years} years
        """
        elements.append(Paragraph(tax_info, self.styles['CustomBody']))
        
        return elements
    
    def _create_analysis_section(self, summary: Dict[str, Any], forecast_df: pd.DataFrame) -> List:
        """Create detailed analysis section."""
        elements = []
        
        elements.append(Paragraph("Detailed Analysis", self.styles['CustomTitle']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Accumulation phase
        working_df = forecast_df[forecast_df['Working'] == True]
        retired_df = forecast_df[forecast_df['Working'] == False]
        
        if not working_df.empty:
            elements.append(Paragraph("Accumulation Phase (Working Years)", self.styles['SectionHeader']))
            
            total_income = working_df['Total Income'].sum()
            total_taxes = working_df['Total Tax'].sum()
            total_saved = working_df['Cash Flow'].sum()
            avg_savings_rate = (total_saved / total_income * 100) if total_income > 0 else 0
            
            accum_info = f"""
            Years Working: {len(working_df)}<br/>
            Total Income Earned: {self._format_currency(total_income)}<br/>
            Total Taxes Paid: {self._format_currency(total_taxes)}<br/>
            Total Amount Saved: {self._format_currency(total_saved)}<br/>
            Average Savings Rate: {avg_savings_rate:.1f}%<br/>
            Assets at Retirement: {self._format_currency(summary.get('retirement_assets', 0))}
            """
            elements.append(Paragraph(accum_info, self.styles['CustomBody']))
            elements.append(Spacer(1, 0.2*inch))
        
        # Retirement phase
        if not retired_df.empty:
            elements.append(Paragraph("Retirement Phase", self.styles['SectionHeader']))
            
            years_in_retirement = len(retired_df)
            total_withdrawals = retired_df['Withdrawal'].sum()
            total_ss = retired_df['Social Security'].sum()
            total_investment_gains = retired_df['Investment Gains'].sum()
            
            retire_info = f"""
            Years in Retirement: {years_in_retirement}<br/>
            Total Withdrawals: {self._format_currency(total_withdrawals)}<br/>
            Total Social Security: {self._format_currency(total_ss)}<br/>
            Total Investment Gains: {self._format_currency(total_investment_gains)}<br/>
            Final Assets: {self._format_currency(summary['final_assets'])}
            """
            elements.append(Paragraph(retire_info, self.styles['CustomBody']))
            elements.append(Spacer(1, 0.2*inch))
        
        # Tax analysis
        elements.append(Paragraph("Tax Analysis", self.styles['SectionHeader']))
        
        total_income_lifetime = forecast_df['Total Income'].sum()
        total_tax_lifetime = forecast_df['Total Tax'].sum()
        effective_tax_rate = (total_tax_lifetime / total_income_lifetime * 100) if total_income_lifetime > 0 else 0
        
        tax_info = f"""
        Total Lifetime Income: {self._format_currency(total_income_lifetime)}<br/>
        Total Lifetime Taxes: {self._format_currency(total_tax_lifetime)}<br/>
        Effective Tax Rate: {effective_tax_rate:.2f}%
        """
        elements.append(Paragraph(tax_info, self.styles['CustomBody']))
        
        return elements
    
    
    def _create_charts_section(self, forecast_df: pd.DataFrame) -> List:
        """Create charts section with key visualizations."""
        elements = []
        
        elements.append(Paragraph("Wealth Projections", self.styles['CustomTitle']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Add note about charts
        note = Paragraph(
            "<i>Note: Interactive charts are available in the web application. "
            "Static chart generation may not be available in all deployment environments.</i>",
            self.styles['CustomBody']
        )
        elements.append(note)
        elements.append(Spacer(1, 0.2*inch))
        
        # 1. Asset Growth Chart
        elements.append(Paragraph("Asset Growth Over Time", self.styles['SectionHeader']))
        asset_chart = self._create_asset_chart(forecast_df)
        if asset_chart:
            elements.append(asset_chart)
        elements.append(Spacer(1, 0.3*inch))
        
        # 2. Income vs Expenses Chart
        elements.append(Paragraph("Income and Expenses", self.styles['SectionHeader']))
        income_chart = self._create_income_expenses_chart(forecast_df)
        if income_chart:
            elements.append(income_chart)
        elements.append(Spacer(1, 0.3*inch))
        
        # 3. Cash Flow Chart
        elements.append(PageBreak())
        elements.append(Paragraph("Annual Cash Flow", self.styles['SectionHeader']))
        cashflow_chart = self._create_cashflow_chart(forecast_df)
        if cashflow_chart:
            elements.append(cashflow_chart)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_asset_chart(self, forecast_df: pd.DataFrame):
        """Create asset growth chart as an image."""
        try:
            # Try using kaleido for plotly export
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=forecast_df['Year'],
                y=forecast_df['Assets (Nominal)'],
                name='Assets (Nominal)',
                line=dict(color='#1f77b4', width=2),
                fill='tozeroy'
            ))
            
            fig.add_trace(go.Scatter(
                x=forecast_df['Year'],
                y=forecast_df['Assets (Real)'],
                name='Assets (Inflation-Adjusted)',
                line=dict(color='#ff7f0e', width=2, dash='dash')
            ))
            
            fig.update_layout(
                title="Asset Growth Projection",
                xaxis_title="Year",
                yaxis_title="Assets ($)",
                height=400,
                showlegend=True,
                legend=dict(x=0, y=1.1, orientation='h')
            )
            
            fig.update_yaxes(tickformat='$,.0f')
            
            # Convert to image using kaleido
            img_bytes = fig.to_image(format="png", width=600, height=400, engine="kaleido")
            img = Image(io.BytesIO(img_bytes), width=6*inch, height=4*inch)
            
            return img
        except Exception as e:
            # Fallback: Create a text placeholder
            return self._create_chart_placeholder("Asset Growth Chart", str(e))
    
    def _create_income_expenses_chart(self, forecast_df: pd.DataFrame):
        """Create income vs expenses chart."""
        try:
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=forecast_df['Year'],
                y=forecast_df['Total Income'],
                name='Total Income',
                marker_color='#27ae60'
            ))
            
            fig.add_trace(go.Bar(
                x=forecast_df['Year'],
                y=forecast_df['Expenses'],
                name='Expenses',
                marker_color='#e74c3c'
            ))
            
            fig.add_trace(go.Bar(
                x=forecast_df['Year'],
                y=forecast_df['Total Tax'],
                name='Taxes',
                marker_color='#95a5a6'
            ))
            
            fig.update_layout(
                title="Income, Expenses, and Taxes",
                xaxis_title="Year",
                yaxis_title="Amount ($)",
                barmode='group',
                height=400,
                showlegend=True,
                legend=dict(x=0, y=1.1, orientation='h')
            )
            
            fig.update_yaxes(tickformat='$,.0f')
            
            # Convert to image
            img_bytes = fig.to_image(format="png", width=600, height=400, engine="kaleido")
            img = Image(io.BytesIO(img_bytes), width=6*inch, height=4*inch)
            
            return img
        except Exception as e:
            return self._create_chart_placeholder("Income & Expenses Chart", str(e))
    
    def _create_cashflow_chart(self, forecast_df: pd.DataFrame):
        """Create cash flow chart."""
        try:
            fig = go.Figure()
            
            # Color code positive and negative cash flow
            colors_list = ['#2ecc71' if x >= 0 else '#e74c3c' for x in forecast_df['Cash Flow']]
            
            fig.add_trace(go.Bar(
                x=forecast_df['Year'],
                y=forecast_df['Cash Flow'],
                name='Net Cash Flow',
                marker_color=colors_list
            ))
            
            fig.add_trace(go.Scatter(
                x=forecast_df['Year'],
                y=forecast_df['Investment Gains'],
                name='Investment Gains',
                line=dict(color='#9b59b6', width=2),
                mode='lines'
            ))
            
            fig.update_layout(
                title="Annual Cash Flow and Investment Gains",
                xaxis_title="Year",
                yaxis_title="Amount ($)",
                height=400,
                showlegend=True,
                legend=dict(x=0, y=1.1, orientation='h')
            )
            
            fig.update_yaxes(tickformat='$,.0f')
            
            # Convert to image
            img_bytes = fig.to_image(format="png", width=600, height=400, engine="kaleido")
            img = Image(io.BytesIO(img_bytes), width=6*inch, height=4*inch)
            
            return img
        except Exception as e:
            return self._create_chart_placeholder("Cash Flow Chart", str(e))
    
    def _create_chart_placeholder(self, chart_name: str, error_msg: str = ""):
        """Create a placeholder when chart cannot be generated."""
        # Create a simple text box explaining charts are not available
        elements = []
        
        text = f"""
        <b>{chart_name}</b><br/>
        <i>Note: Charts cannot be displayed in PDF format on this platform.</i><br/>
        <font size="8">Please view interactive charts in the Streamlit app.</font>
        """
        
        if error_msg and "kaleido" in error_msg.lower():
            text += "<br/><font size=\"7\" color=\"gray\">(Chart rendering requires local installation)</font>"
        
        para = Paragraph(text, self.styles['CustomBody'])
        
        # Create a simple table as a visual placeholder
        data = [
            [chart_name],
            ['Interactive charts available in the web application']
        ]
        
        table = Table(data, colWidths=[6*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#374151')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('BOX', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.grey),
        ]))
        
        return table
    
    def _create_comprehensive_data_table(self, forecast_df: pd.DataFrame) -> List:
        """Create comprehensive year-by-year data tables."""
        elements = []
        
        elements.append(Paragraph("Year-by-Year Projection", self.styles['CustomTitle']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Key columns to include
        key_cols = ['Year', 'Age', 'Total Income', 'Expenses', 'Total Tax', 'Cash Flow', 'Assets (Nominal)']
        
        # Show first 20 years
        elements.append(Paragraph("First 20 Years", self.styles['SectionHeader']))
        first_years = forecast_df.head(20)[key_cols] if len(forecast_df) >= 20 else forecast_df[key_cols]
        elements.extend(self._create_formatted_data_table(first_years))
        
        # Show middle years (sample every 5 years if forecast is long)
        if len(forecast_df) > 40:
            elements.append(PageBreak())
            elements.append(Paragraph("Middle Years (Every 5 Years)", self.styles['SectionHeader']))
            middle_start = 20
            middle_end = len(forecast_df) - 20
            middle_years = forecast_df.iloc[middle_start:middle_end:5][key_cols]
            elements.extend(self._create_formatted_data_table(middle_years))
        
        # Show last 20 years
        if len(forecast_df) > 20:
            elements.append(PageBreak())
            elements.append(Paragraph("Final 20 Years", self.styles['SectionHeader']))
            last_years = forecast_df.tail(20)[key_cols]
            elements.extend(self._create_formatted_data_table(last_years))
        
        return elements
    
    def _create_formatted_data_table(self, df: pd.DataFrame) -> List:
        """Create a formatted data table segment."""
        elements = []
        
        # Format the dataframe
        display_df = df.copy()
        
        # Format currency columns
        for col in ['Total Income', 'Expenses', 'Total Tax', 'Cash Flow', 'Assets (Nominal)']:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: f"${x:,.0f}")
        
        display_df['Year'] = display_df['Year'].astype(int)
        display_df['Age'] = display_df['Age'].astype(int)
        
        # Convert to list for table
        data = [display_df.columns.tolist()] + display_df.values.tolist()
        
        # Create table with adjusted column widths
        col_widths = [0.6*inch, 0.6*inch, 1.2*inch, 1.1*inch, 1.0*inch, 1.1*inch, 1.4*inch]
        table = Table(data, colWidths=col_widths)
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('TOPPADDING', (0, 1), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _format_currency(self, value: float) -> str:
        """Format value as currency."""
        return f"${value:,.0f}"

