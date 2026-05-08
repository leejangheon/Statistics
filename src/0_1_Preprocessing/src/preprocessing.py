import pandas as pd
import os
import sys
import re
from io import StringIO
from collections import Counter

class DataPreprocessor:
    def __init__(self, args):
        self.args = args
        self.results = {}
        self.tax_mapping = {}
        self.func_mapping = {}
        self.custom_mapping = {}
        self.metadata = None
        self.group_col = None
            
        self.tax_keywords = {
            'phylum': 'Phylum', 'class': 'Class', 'order': 'Order',
            'family': 'Family', 'genus': 'Genus', 'species': 'Species',
            'l2': 'Phylum (L2)', 'l3': 'Class (L3)', 'l4': 'Order (L4)',
            'l5': 'Family (L5)', 'l6': 'Genus (L6)', 'l7': 'Species (L7)',
            'l8': 'MAG (L8)', 'mag': 'MAG', 'asv': 'ASV'
        }
        self.func_keywords = {
            'genefamilies': 'GeneFamilies', 
            'genefamily': 'GeneFamily',
            'pathabundance': 'PathAbundance',
            'eggnog': 'eggNOG',
            'kegg': 'KEGG',
            'pfam': 'Pfam'
        }

    def execute(self):
        """Main execution pipeline for preprocessing."""
        self._load_metadata()
        self._map_files()
        self._print_summary()

        if self.args.adiv:
            self._process_alpha_div()

        if self.tax_mapping:
            if self.args.type == 'asv':
                self._process_taxonomy_asv()
            elif self.args.type == 'mag':
                self._process_taxonomy_mag()
            elif self.args.type == 'read-based':
                self._process_taxonomy_read()

        if self.func_mapping:
            self._process_functional()

        if self.custom_mapping:
            self._process_custom()

        print(f"\n[DONE] Preprocessing completed for all files.")
        
    def _load_metadata(self):
        print(f"[*] Loading Metadata: {self.args.metadata}")
        try:
            df = pd.read_csv(self.args.metadata, sep='\t',dtype=str)
            df.set_index(df.columns[0], inplace=True)
            self.group_col = df.columns[0]
            self.metadata = df
            print(f"    > Found {len(df)} samples and Group column: '{self.group_col}'")
        except Exception as e:
            print(f"Error loading metadata: {e}")
            sys.exit(1)

    def _map_files(self):
        if self.args.input_tax:
            for path in self.args.input_tax:
                fname = os.path.basename(path).upper()
                tool_label = "MAG" if self.args.type == "mag" else "READ" if self.args.type == "read-based" else "DB"
                if "BLAST" in fname: tool_label = "BLAST"
                elif "VSEARCH" in fname: tool_label = "VSEARCH"
                elif "BAYESIAN" in fname: tool_label = "Bayesian"
                for kw in self.tax_keywords:
                    if kw in fname.lower():
                        unique_key = f"{tool_label}_{kw}"
                        self.tax_mapping[unique_key] = path
                        break

        if self.args.input_func:
            for path in self.args.input_func:
                fname = os.path.basename(path).lower()
                for kw in self.func_keywords:
                    if kw in fname:
                        self.func_mapping[kw] = path
                        break
    
        if hasattr(self.args, 'input_custom') and self.args.input_custom:
            for path in self.args.input_custom:
                fname = os.path.basename(path)
                self.custom_mapping[fname] = path

    def _sync_with_metadata(self, df, name):
        metadata_ids = self.metadata.index.tolist()
        print(metadata_ids)
        col_match = len(set(metadata_ids) & set(df.columns))
        row_match = len(set(metadata_ids) & set(df.index))
        if row_match > col_match: df = df.T
        current_data_samples = set(df.columns)
        missing_samples = set(metadata_ids) - current_data_samples
        if missing_samples:
            print(f"\n[ERROR] Missing samples in '{name}': {sorted(list(missing_samples))}")
            sys.exit(1)
        return df[metadata_ids]

    def _print_summary(self):
        print("\n" + "="*35 + "\n [ Preprocessing Summary ] \n" + "="*35)
        print(f"TYPE    : {self.args.type.upper()}")    
        print(f"METADATA: {os.path.basename(self.args.metadata)} ({len(self.metadata)} samples)")
        print("\n[Taxonomy input]")
        for key, path in self.tax_mapping.items(): print(f"{key:15}: {os.path.basename(path)}")
        print("\n[Functional input]")
        for key, path in self.func_mapping.items(): print(f"{key:15}: {os.path.basename(path)}")
        print("\n" + "="*35 + "\n")

    def _process_custom(self):
        for fname, path in self.custom_mapping.items():
            name_only = os.path.splitext(fname)[0]
            print(f"[*] Processing Custom Input: {fname}")

            df = self._load_file(path)
            df_sync = self._sync_with_metadata(df, f"Custom_{name_only}")
            os.makedirs(self.args.output, exist_ok=True)
            
            # out_path = os.path.join(self.args.output, f"processed_custom_{name_only}.txt")
            out_path = os.path.join(self.args.output, "processed.txt")
            
            df_sync.to_csv(out_path, sep='\t', index_label="label")
            print(f"    [-->] Saved: {os.path.basename(out_path)}")

    def _process_taxonomy_asv(self):
        for unique_key, path in self.tax_mapping.items():
            tool_label, kw = unique_key.split('_', 1)
            print(f"[*] Processing ASV Taxonomy: {tool_label} - {kw.upper()}")
            with open(path, 'r') as f: lines = f.readlines()
            filtered_lines = [l for l in lines if not l.startswith('# Constructed from biom file')]
            if filtered_lines and filtered_lines[0].startswith('#'): filtered_lines[0] = filtered_lines[0].lstrip('#')
            df = pd.read_csv(StringIO("".join(filtered_lines)), sep='\t', index_col=0)*100
            df_sync = self._sync_with_metadata(df, f"ASV_{tool_label}_{kw}")
            level_match = re.search(r'l(\d+)', kw.lower()); target_level = int(level_match.group(1)) if level_match else 7
            processed_index, mapping_df = self._parse_taxonomy_string(df_sync.index, target_level)
            df_sync.index = processed_index
            self._write_files(df_sync, mapping_df, f"tax_{tool_label}_{kw.upper()}")

    def _process_taxonomy_mag(self):
        for unique_key, path in self.tax_mapping.items():
            tool_label, kw = unique_key.split('_', 1)
            print(f"[*] Processing MAG Taxonomy: {kw.upper()}")
            df = pd.read_csv(path, sep='\t')
            taxon_levels = ['Kingdom', 'Phylum', 'Class', 'Order', 'Family', 'Genus', 'Species']
            available_levels = [lvl for lvl in taxon_levels if lvl in df.columns]
            df['full_taxon'] = df[available_levels].apply(lambda x: ';'.join(x.values.astype(str)), axis=1)
            if 'MAG' in df.columns and 'l8' in kw.lower():
                df['final_label'] = df['MAG']; df['final_desc'] = df['Most Similar Taxonomy']
            else:
                df['final_label'] = df['Most Similar Taxonomy']; df['final_desc'] = ""
            name_counts = Counter(df['final_label']); current_usage = {}; unique_labels = []
            for name in df['final_label']:
                if name_counts[name] > 1:
                    count = current_usage.get(name, 0) + 1; current_usage[name] = count
                    unique_labels.append(f"{name} [{count}]")
                else: unique_labels.append(name)
            df['final_label'] = unique_labels
            sample_cols = [col for col in df.columns if col in self.metadata.index]
            abundance_df = df.set_index('final_label')[sample_cols]
            abundance_sync = self._sync_with_metadata(abundance_df, f"MAG_{kw}")
            mapping_df = pd.DataFrame({'label': df['final_label'].values, 'description': df['final_desc'].values, 'taxon': df['full_taxon'].values})
            self._write_files(abundance_sync, mapping_df, f"tax_MAG_{kw.upper()}")

    def _process_taxonomy_read(self):
        for unique_key, path in self.tax_mapping.items():
            _, kw = unique_key.split('_', 1)
            print(f"[*] Processing Read-based Taxonomy: {kw.upper()}")
            df = pd.read_csv(path, sep='\t')
            label_col = df.columns[0]; original_labels = df[label_col].astype(str).tolist()
            name_counts = Counter(original_labels); current_usage = {}; unique_labels = []
            for name in original_labels:
                if name_counts[name] > 1:
                    count = current_usage.get(name, 0) + 1; current_usage[name] = count
                    unique_labels.append(f"{name} [{count}]")
                else: unique_labels.append(name)
            df['final_label'] = unique_labels
            sample_cols = [col for col in df.columns if col in self.metadata.index]
            abundance_df = df.set_index('final_label')[sample_cols]
            abundance_sync = self._sync_with_metadata(abundance_df, f"READ_{kw}")
            mapping_df = pd.DataFrame({'label': unique_labels, 'description': "", 'taxon': original_labels})
            self._write_files(abundance_sync, mapping_df, f"tax_READ_{kw.upper()}")

    def _parse_taxonomy_string(self, original_index, target_level):
        temp_names = []; mapping_rows = []; level_initials = ['k', 'p', 'c', 'o', 'f', 'g', 's']
        invalid_names = {'unassigned', 'unknown', 'none', '', 'other', 'na'}
        for raw_tax in original_index:
            parts = [p.strip() for p in raw_tax.split(';')]; limited_parts = parts[:target_level]
            final_name = ""; last_idx = len(limited_parts) - 1
            for i in range(last_idx, -1, -1):
                # [Corrected Regex] from '^[a-z]__-->' to '^[a-z]__?'
                name_val = re.sub(r'^[a-z]__?', '', limited_parts[i]).replace('__', ' ').strip()
                if name_val and name_val.lower() not in invalid_names:
                    if i == last_idx: final_name = name_val
                    else: final_name = f"Unknown_{level_initials[i]}_{name_val}"
                    break
            if not final_name: final_name = "Other"
            temp_names.append(final_name); mapping_rows.append({'label': '', 'description': '', 'taxon': raw_tax})
        name_counts = Counter(temp_names); final_unique_names = []; current_usage = {}
        for name in temp_names:
            if name_counts[name] > 1:
                count = current_usage.get(name, 0) + 1; current_usage[name] = count
                final_unique_names.append(f"{name} [{count}]")
            else: final_unique_names.append(name)
        for idx, u_name in enumerate(final_unique_names): mapping_rows[idx]['label'] = u_name
        return final_unique_names, pd.DataFrame(mapping_rows)

    def _process_functional(self):
        """Process functional data with strict separation of Filtered and w.taxon."""
        for kw, path in self.func_mapping.items():
            print(f"[*] Processing Functional: {kw.upper()}")
            df = pd.read_csv(path, sep='\t', index_col=0)
            
            invalid_patterns = ['UNMAPPED', 'UNGROUPED', 'NO_NAME']
            mask = df.index.str.contains('|'.join(invalid_patterns), case=False, na=False)
            df_cleaned = df[~mask]
            
            has_taxon_mask = df_cleaned.index.str.contains(r'\|', na=False)
            
            df_filtered = df_cleaned[~has_taxon_mask]
            df_w_taxon = df_cleaned[has_taxon_mask]
            
            if not df_filtered.empty:
                self._handle_functional_mode(df_filtered, kw, "filtered")
            if not df_w_taxon.empty:
                self._handle_functional_mode(df_w_taxon, kw, "w.taxon")

    def _handle_functional_mode(self, df, kw, mode):
        parsed_mapping = []
        new_indices = []
        
        for full_idx in df.index:
            taxon_parts = full_idx.split('|')
            taxon = taxon_parts[1].strip() if len(taxon_parts) > 1 else ""
            main_part = taxon_parts[0].strip()
            
            id_desc_parts = main_part.split(':', 1)
            accession_id = id_desc_parts[0].strip()
            description = id_desc_parts[1].strip() if len(id_desc_parts) > 1 else ""
            
            if mode == "filtered":
                if '|' in full_idx: continue 
                label = accession_id
                mapping_entry = {'label': label, 'description': description, 'taxon': ""}
            else:
                if '|' not in full_idx: continue
                label = f"{accession_id}_{taxon}"
                mapping_entry = {'label': label, 'id': accession_id, 'description': description, 'taxon': taxon}
                
            new_indices.append(label)
            parsed_mapping.append(mapping_entry)
            
        if not new_indices: return
        df_parsed = df.iloc[:len(new_indices)].copy()
        df_parsed.index = new_indices
        
        df_sync = self._sync_with_metadata(df_parsed, f"Func_{mode}_{kw}")
        mapping_df = pd.DataFrame(parsed_mapping)
        self._write_files(df_sync, mapping_df, f"func_{mode}_{kw}")

    def _write_files(self, processed_df, mapping_df, kw):
        """Save results as processed.txt / mapping.txt with special case for w.taxon."""
        os.makedirs(self.args.output, exist_ok=True)
        cols = ['label', 'id', 'description', 'taxon']
        mapping_df = mapping_df[[c for c in cols if c in mapping_df.columns]]
        
        # [Modified] Unified naming logic
        if "w.taxon" in kw:
            p_name = "processed_w.taxon.txt"
            m_name = "mapping_w.taxon.txt"
        else:
            p_name = "processed.txt"
            m_name = "mapping.txt"

        processed_path = os.path.join(self.args.output, p_name)
        mapping_path = os.path.join(self.args.output, m_name)

        # processed_df.to_csv(os.path.join(self.args.output, f"processed_{kw}.txt"), sep='\t', index_label="label")
        # mapping_df.to_csv(os.path.join(self.args.output, f"mapping_{kw}.txt"), sep='\t', index=False)
        
        processed_df.to_csv(processed_path, sep='\t', index_label="label")
        mapping_df.to_csv(mapping_path, sep='\t', index=False)
        
        print(f"    [-->] Saved: {p_name} / {m_name}")

    def _load_file(self, path):
        sep = '\t' if path.endswith(('.tsv', '.txt')) else ','
        df = pd.read_csv(path, sep=sep, index_col=0)
        df.index = df.index.astype(str)
        return df

    def _process_alpha_div(self):
        df = self._load_file(self.args.adiv)
        processed_df = self._sync_with_metadata(df, "AlphaDiv")
        mapping_data = pd.DataFrame({'label': processed_df.index, 'description': processed_df.index, 'taxon': ""})
        self._write_files(processed_df, mapping_data, "adiv")
