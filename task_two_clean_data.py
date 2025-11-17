import pandas as pd
import os
import glob
import yaml
import sys 

# --- CONFIGURATION LOADING ---
def load_config(config_path='task_two_config.yaml'):
    """
    Loads configuration settings from a YAML file.
    Exits if the file is not found or cannot be parsed.
    """
    try:
        # Use 'r' mode for reading the YAML file
        with open(config_path, 'r') as f:
            # Use safe_load for security
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_path}' not found.")
        print("Please ensure task_two_config.yaml is in the same directory as the script.")
        # Exit the application cleanly upon critical failure
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        sys.exit(1)

# --- CORE PROCESSING LOGIC ---
def process_sales_data(config):
    """
    Parses all CSV files in the configured data directory, filters by product,
    calculates sales, and saves the summary to the output_file with currency symbols re-attached.
    """
    # Extract parameters from the loaded configuration
    data_dir = config.get('data_directory', 'data')
    product_filter = config.get('product_filter', 'pink morsel')
    default_symbol = config.get('default_currency_symbol', '$')
    
    # Generate the output filename dynamically
    output_file = f"{product_filter.replace(' ', '_').lower()}_sales_summary.csv"

    print(f"\nStarting data processing for product '{product_filter}' from directory: {data_dir}...")
    print(f"Check README and config file 'task_two_config.yaml' for more info")
    

    all_filtered_data = []
    
    # currency_symbol will hold the symbol used for final output (first detected symbol or default)
    currency_symbol = None 
    
    # Find all CSV files in the configured directory
    csv_files = glob.glob(os.path.join(data_dir, '*.csv'))

    if not csv_files:
        if not os.path.exists(data_dir):
            print(f"Error: The directory '{data_dir}' was not found.")
        else:
            print(f"Error: No CSV files found in {data_dir}. Please check your 'data_directory' setting in task_two_config.yaml.")
        return

    for file_path in csv_files:
        try:
            print(f"Processing {file_path}...")
            df = pd.read_csv(file_path)

            # 1. Filter using the configured product name (most efficient place)
            pink_morsel_df = df[df['product'] == product_filter].copy()

            if pink_morsel_df.empty:
                print(f"   -> No '{product_filter}' entries in this file. Skipping.")
                continue

            # --- DATA CLEANING & CONVERSION ---
            
            # Initialize flags
            slice_start_index = 0
            
            # 2. SYMBOL DETECTION & SLICING CONTROL (only executes on the first file with data)
            if currency_symbol is None:
                first_price_string = pink_morsel_df['price'].dropna().iloc[0] if not pink_morsel_df['price'].dropna().empty else None
                
                if first_price_string and len(first_price_string) > 0:
                    # Symbol found, set it and prepare to slice
                    currency_symbol = first_price_string[0]
                    slice_start_index = 1
                else:
                    # No price data found in this file's pink morsel entries, use default and don't slice
                    currency_symbol = default_symbol
                    slice_start_index = 0
            else:
                # After the first file, we assume the format is consistent with the detected symbol (or lack thereof)
                # If we detected a symbol earlier, we need to slice now.
                if currency_symbol != default_symbol:
                    slice_start_index = 1
                # If currency_symbol == default_symbol, it means we didn't find a symbol in the first relevant file, so we keep slice_start_index = 0
            
            # 3. CLEAN PRICE: Use the determined slice_start_index for the current DataFrame.
            pink_morsel_df['price_clean_str'] = (
                pink_morsel_df['price']
                .astype(str)
                .str.slice(slice_start_index) 
            )
            
            # 4. Convert price to CENTS using reusable variables
            # Convert to numeric (errors='coerce' handles non-price data gracefully)
            price_numeric = pd.to_numeric(pink_morsel_df['price_clean_str'], errors='coerce').fillna(0)
            price_cents = (price_numeric * 100).astype(int)

            # 5. Calculate Sales in CENTS (Exact Integer Arithmetic)
            quantity = pink_morsel_df['quantity'].fillna(0)
            sales_cents = price_cents * quantity
            
            # 6. Convert final sales figure back to Dollars (float format for internal use)
            sales_numeric = sales_cents / 100.0
            
            # -------------------------------------------------------------------------

            # 7. Select and rename required columns
            summary_df = pink_morsel_df.assign(
                sales=sales_numeric
            )[['sales', 'date', 'region']]

            all_filtered_data.append(summary_df)

        except pd.errors.EmptyDataError:
            print(f"   -> Skipping empty file: {file_path}")
        except FileNotFoundError:
            print(f"   -> File not found: {file_path}")
        except Exception as e:
            # Provide verbose error logging for better debugging
            print(f"   -> Error processing file {file_path} for product '{product_filter}': {e}. Check data integrity.")
            continue

    if not all_filtered_data:
        print("\n--- Processing Complete ---")
        print(f"No '{product_filter}' data was successfully extracted from any file.")
        return

    final_summary_df = pd.concat(all_filtered_data, ignore_index=True)
    
    # --- FORMATTING ---
    
    # Ensure currency_symbol is not None (should only be None if all files were empty)
    if currency_symbol is None:
        currency_symbol = default_symbol 

    # Format the numeric 'sales' column back into a currency string for reporting
    final_summary_df['sales'] = final_summary_df['sales'].apply(
        lambda x: f"{currency_symbol}{x:.2f}"
    )

    # Save the final DataFrame
    final_summary_df.to_csv(output_file, index=False)
    print(f"\n--- Processing Complete ---")
    print(f"Total '{product_filter}' sales records found: {len(final_summary_df)}")
    print(f"Results saved to: {output_file}")

# --- EXECUTION ---
if __name__ == '__main__':
    # 1. Load configuration from YAML
    config = load_config()
    
    # 2. Pass configuration to the main processing function
    process_sales_data(config)