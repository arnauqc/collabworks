import pandas as pd
import networkx as nx
import time
import sys
import glob
import numpy as np
from unidecode import unidecode


def get_search_engine_parameters(search_engine, nodes_size):

    if search_engine == 's':
        search_engine_dict = {'authors_name_column_id': 'Authors', 'authors_separator': ';', 'engine_name': 'Scopus',
                              'unique_articles_column_id': 'EID',
                              'data_files_format': 'csv', 'data_files_column_separator': '',
                              'number_citations_column_id': 'Cited by'}

        if nodes_size == 'a':
            search_engine_dict['node_size_mode'] = 'a'
        else:
            search_engine_dict['node_size_mode'] = 'c'
    else:
        search_engine_dict = {'authors_name_column_id': 'AU', 'unique_articles_column_id': 'UT',
                              'data_files_format': 'txt', 'data_files_column_separator': '\t',
                              'authors_separator': ';',  'number_citations_column_id': 'TC',
                              'engine_name': 'WoS'}

        if nodes_size == 'a':
            search_engine_dict['node_size_mode'] = 'a'
        else:
            search_engine_dict['node_size_mode'] = 'c'

    return search_engine_dict


def get_concat_df(engine_params):
    all_files = glob.glob("./data/*." + engine_params['data_files_format'])
    df_list = []
    for file in all_files:
        if engine_params['engine_name'] == 'WoS':
            part_df = pd.read_csv(file, sep=engine_params['data_files_column_separator'], encoding='utf-8-sig', index_col=False,
                              header=0)
        else:
            part_df = pd.read_csv(file, encoding='utf-8-sig', index_col=False, header=0)
        df_list.append(part_df)

    # Concatenate DataFrames specified in the list
    df = pd.concat(df_list)
    # Drop duplicates based on the WOS Unique Identifier or the Scopus EID.
    filtered_df = df.drop_duplicates(engine_params['unique_articles_column_id'])
    return filtered_df


# Print iterations progress
def print_progress(iteration, total, prefix='', suffix='', decimals=2, bar_length=60):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : number of decimals in percent complete (Int)
        barLength   - Optional  : character length of bar (Int)
    """
    filled_length = int(round(bar_length * iteration / float(total)))
    percents = round(100.00 * (iteration / float(total)), decimals)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),
    sys.stdout.flush()
    if iteration == total:
        sys.stdout.write('\n')
        sys.stdout.flush()


def authors_format(ds, engine_params):
    # Setting the appropriate name format. Removing parentheses in order to avoid regex matching groups
    if engine_params['engine_name'] == 'WoS':
        ds = ds.apply(lambda element: unidecode(str(element).upper().replace(' ', '').replace(',', ', ')
                                                .replace('(', ' ').replace(')', '')))
    else:
        ds = ds.apply(lambda element: unidecode(str(element).upper().replace(' ', '')
                      .replace('(', ' ').replace(')', '').replace('.,','.;')))
    return ds


def populate_adj_matrix(ds, authors_set_list, engine_params):
    """
    This module initializes and populates and adjacency matrix (DataFrame) based on the rows of a Serie, which contains
    in each row the set of authors co-involved in a scientific publication.

    :param ds: Co-autorship Series
    :param authors_set_list: Set of authors contained in co-autorship Serie
    :param engine_params: Dict containing all search engine parameters
    :return: Adjacency Matrix (DataFrame)
    """
    print("\n3) Building network...\n")
    # Get number of authors
    num_authors = len(authors_set_list)
    # Create Adjacency matrix. Array of 0s of len². Indexes and columns has author's names
    adj_df = pd.DataFrame([[0]*num_authors]*num_authors, columns=authors_set_list, index=authors_set_list)
    # Index progress bar
    i = 0
    for author_name in authors_set_list:
        # Filter Series for author name. Regex matching
        author_collaborators_ds = ds[ds.str.contains(author_name + '(?:$|\W)')]
        split_author_collaborators_ds = author_collaborators_ds.str.split(engine_params['authors_separator'])
        column_author_collaborators_df = pd.DataFrame({i: split_author_collaborators_ds.str[i]
                                                       for i in range(max(split_author_collaborators_ds.str.len()))})
        value_counts_author_collaborations_ds = pd.Series(column_author_collaborators_df.stack().values).value_counts()
        value_counts_author_collaborations_ds.drop(author_name, inplace=True)
        adj_df.loc[author_name, value_counts_author_collaborations_ds.index] = value_counts_author_collaborations_ds
        # Step in progress bar
        i += 1
        print_progress(i, num_authors)

    return adj_df


def get_adjacency_df(main_df, min_weight, engine_params):
    """

    :param main_df: Main DataFrame. Contains all the article's information
    :param min_weight: Minimum number of articles that some author must have in order to appear in the graph
    :param engine_params: Dictionary of parameters
    :return:
    """
    print("\n2) Building authors sets...")
    # Select column which contains the Authors names
    ds = main_df[engine_params['authors_name_column_id']]
    ds = authors_format(ds, engine_params)
    # Number of articles within the current Series
    num_articles = len(ds)
    # List of all appearances of authors names
    all_authors_appearance_list = [author for row in ds for author in row.split(engine_params['authors_separator'])]
    # Series all appearances of authors names
    all_authors_appearance_ds = pd.Series(all_authors_appearance_list)
    # Value counts (histogram) of all_authors_appearance_ds
    authors_histogram_ds = all_authors_appearance_ds.value_counts()
    # Set of authors names
    authors_set = set(all_authors_appearance_list)
    # List of authors_set
    authors_set_list = list(authors_set)

    # Obtain the adjacency DF based on the co-authorship Series
    adj_df = populate_adj_matrix(ds, authors_set_list, engine_params)

    # Filter the authors of the adjacency matrix based on the number of publication.
    # The min weight represents the number of minimum publications
    # some author ought have not to be dropped from the adjacency matrix.
    author_to_be_deleted_list = list(authors_histogram_ds[authors_histogram_ds < min_weight].index)
    # Drop the authors to be deleted from the adjacency matrix.
    # First from axis 0 (horizontal) and the from the vertical (1) one
    adj_df.drop(author_to_be_deleted_list, axis=0)
    adj_df.drop(author_to_be_deleted_list, axis=1)
    # Delete authors which are less relevant than imposed by the threshold
    authors_set_list = [author for author in authors_set_list if author not in author_to_be_deleted_list]
    # Order columns and indexes in the same authors order
    adj_df = adj_df.ix[authors_set_list, authors_set_list]

    return adj_df, authors_set_list, authors_histogram_ds


def get_num_articles(G, number_of_articles_per_author_ds, authors_tuple):
    # Maximum number of publications found in the Dataframe
    x_max = number_of_articles_per_author_ds.max()
    # Maximum size of the nodes
    size_max = 13
    k = (x_max/size_max)
    for i in range(len(authors_tuple)):
        # Set a relation between node identifier and author name
        G.node[i]['Label'] = authors_tuple[i]
        # Set the number of articles normalized as the node size property
        # x_i: Number of publications of the author
        x_i = number_of_articles_per_author_ds[authors_tuple[i]]
        if x_i >= k:
            G.node[i]['size'] = str(int(x_i/k + k))
        else:
            G.node[i]['size'] = str(x_i + 1)

    return G


def get_citations_author(G, main_df, authors_tuple, engine_params):
    main_df[engine_params['authors_name_column_id']] = \
        authors_format(main_df[engine_params['authors_name_column_id']], engine_params)
    for i in range(len(authors_tuple)):
        # Return authors name from the tuple given an index i
        author_name = authors_tuple[i]
        # Obtain a new Dataframe based on the author name appearance (as a substring) on the authors name column
        substring_researcher_df = \
            main_df[main_df[engine_params['authors_name_column_id']].str.contains(author_name + '(?:$|\W)')]
        # Obtain the total number of citations. Regex is used (\D, only digits will be kept).
        number_citations_author = substring_researcher_df[engine_params['number_citations_column_id']].astype('int').sum()

        # Set a relation between node identifier and author name
        G.node[i]['Label'] = author_name
        # Set the number of articles normalized as the node size property. The normalisation function will be a 1/4
        # exponent power function.
        # c_i: Normalized Number of citations of the author
        c_i = int(np.power(number_citations_author, 0.25)) + 1
        G.node[i]['size'] = str(c_i)

    return G


def export_graph(main_df, publications_threshold, engine_params):
    # Lets begin dropping all NAN from authors names column and reset index
    main_df.dropna(subset=[engine_params['authors_name_column_id']], inplace=True)
    main_df.reset_index(inplace=True)

    # Obtain the adjacency matrix over a Pandas DF
    authors_adjacency_df, authors_tuple, number_of_articles_per_author_ds = \
        get_adjacency_df(main_df, publications_threshold, engine_params)

    # Based on the generated adjacency matrix, obtain the networkX graph
    G = nx.from_numpy_matrix(authors_adjacency_df.values)

    # NODES SIZE BASED ON THE NUMBER OF CITATIONS PER AUTHOR
    if engine_params['node_size_mode'] == 'c':
        print('\n4) Calculating nodes sizes based on the # citations per author...')
        G = get_citations_author(G, main_df, authors_tuple, engine_params)
        # Proceed to export the obtained networkX graph to a GraphML network
        print("\n5) Exporting network...\n")
        nx.write_graphml(G, 'Graph [' + engine_params['engine_name'] + ' - Threshold ' + str(publications_threshold) +
                         ' - # Citations].graphml')

    else:
        # NODES SIZE BASED ON THE NUMBER OF PUBLICATIONS PER AUTHOR
        print('\n4) Calculating nodes sizes based on the # articles per author...\n')
        G = get_num_articles(G, number_of_articles_per_author_ds, authors_tuple)
        # Proceed to export the obtained networkX graph to a GraphML network
        print("5) Exporting network...\n")
        nx.write_graphml(G, 'Graph [' + engine_params['engine_name'] + ' - Threshold ' + str(publications_threshold) +
                         ' - # Articles].graphml')


if __name__ == "__main__":
    print("\n\nCOLLABWORKS")
    print("Python WoS/Scopus collaboration networks tool\n")
    args = sys.argv[1:]
    if args:
        # Input files must be placed in data folder.
        # Input files ought be named DOI_code-references.txt
        # Script unique argument stands for the threshold weight from
        # which lower contributors will not be taken account.
        # The min weight represents the number of minimum publications
        # some author ought have not to be dropped from the adjacency matrix. Default value: 1
        print('\n -- Network properties -- ')
        weight_threshold = [item for item in args if item.isdigit()]
        if weight_threshold:
            weight_threshold = int(weight_threshold[0])
            print("   - Publications threshold equal to ", weight_threshold)
        else:
            weight_threshold = 1
            print("   - No publication threshold specified. It will be set equal to 1.")
        if '-s' in args:
            # If Scopus is the search engine
            print("   - Using Scopus as default scientific DataBase")
            if '-a' in args:
                print('   - Nodes size will be calculated based on the number of articles per author')
                engine_params_dict = get_search_engine_parameters('s', 'a')
            else:
                print('   - Nodes size will be calculated based on the number of citacions per author')
                engine_params_dict = get_search_engine_parameters('s', 'c')

        else:
            # If WoS is the search engine
            print("   - Using WoS as default scientific DataBase")
            if '-a' in args:
                print('   - Nodes size will be calculated based on the number of articles per author')
                engine_params_dict = get_search_engine_parameters('w', 'a')
            else:
                print('   - Nodes size will be calculated based on the number of citacions per author')
                engine_params_dict = get_search_engine_parameters('w', 'c')

    else:
        print('   - Publications threshold unset.\n'
              '   - WoS set as default search engine\n'
              '   - Nodes size will be calculated based on the number of citacions per author\n')
        weight_threshold = 1
        engine_params_dict = get_search_engine_parameters('w', 'c')

    tic = time.time()

    print("\n\n1) Building concatenated database...")
    df = get_concat_df(engine_params_dict)
    export_graph(df, weight_threshold, engine_params_dict)

    tac = time.time()
    time_needed = int(tac - tic)
    m, s = divmod(time_needed, 60)
    h, m = divmod(m, 60)
    string_time = str(int(h)) + 'h ' + str(int(m)) + 'm ' + str(int(s)) + 's'
    print('\nExecution time: ' + string_time)
