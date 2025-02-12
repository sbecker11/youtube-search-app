from dynamodb_utils.dbtypes import *

class DynamoDbFilterUtils:

    @staticmethod
    def select_dbItems_by_dbAttrs(
        dbItems: List[DbItem],
        select_by_dbAttrs: List[DbAttr]
    ) -> List[DbItem]:
        """
        Returns a list of dbItems with only the selected attributes.

        :param dbItems: The list of dbItems to filter.
        :param select_by_dbAttrs: List of DbAttrs to include in each dbItem.
        :return: A new list of dbItems containing only the specified attributes.
        """
        # Check if inputs are valid before processing
        if not dbItems or not select_by_dbAttrs:
            return []

        filtered_dbItems = []
        for dbItem in dbItems:
            # Use dictionary comprehension for clearer and more Pythonic code
            filtered_dbItem = {attr: dbItem.get(attr) for attr in select_by_dbAttrs if attr in dbItem}
            filtered_dbItems.append(filtered_dbItem)

        return filtered_dbItems

    @staticmethod
    def test_select_dbItems_by_dbAttrs():
        """
        Test the select_dbItems_by_dbAttrs function with predefined data.
        """
        # Test data
        test_dbItems = [
            {"name": "Alice", "age": 30, "score": 85},
            {"name": "Bob", "age": 25, "score": 90},
            {"name": "Charlie", "age": 35, "score": 80},
            {"name": "David", "age": 25, "score": 88}
        ]

        # Select these dbAttrs among all dbItems
        test_select_by_dbAttrs = ["age","score"]

        result = DynamoDbFilterUtils.select_dbItems_by_dbAttrs(test_dbItems, test_select_by_dbAttrs)

        # Expected result after select by dbAttrs
        expected_filtered_dbItems = [
            {"age": 30, "score": 85},
            {"age": 25, "score": 90},
            {"age": 35, "score": 80},
            {"age": 25, "score": 88}
        ]

        # Check if the result matches expected filtered
        assert result == expected_filtered_dbItems, f"Test failed. Expected {expected_filtered_dbItems}, but got {result}"
        print("Filtered test passed successfully!")


    @staticmethod
    def test_select_distinct_values_by_dbAttrs():
        """
        Test find distinct values among all dbItems in the given select_by dbAttrs
        """
        # Test data
        test_dbItems = [
            {"response.queryDetails.q":"SpaceX"},
            {"response.queryDetails.q":"Agentful"},
            {"response.queryDetails.q":"SpaceX"}
        ]

        # Select these dbAttrs among dbItems
        test_select_by_dbAttrs = ["respnse.queryDetails.q"]

        # Expected result after select by dbAttrs
        expected_filtered_dbItems = [
            {"response.queryDetails.q":"SpaceX"},
            {"response.queryDetails.q":"Agentful"},
            {"response.queryDetails.q":"SpaceX"}
        ]

        # Now find distinct values for the given dbAttrs among all dbItems
        result_distinct_values = {}
        dbItems = expected_filtered_dbItems
        for dbAttr in test_select_by_dbAttrs:
            result_distinct_values[dbAttr] = set( dbItem[dbAttr] for dbItem in dbItems )

        # the expected sets of distinct values for each dbAttr
        expected_distinct_values = {}
        expected_distinct_values['response.queryDetails.q'] = set(["SpaceX","Agentful"])

        # compare the resulting sets of distinct values to the expected sets of disinct values
        for dbAttr in test_select_by_dbAttrs:
            assert result_distinct_values[dbAttr] == expected_distinct_values[dbAttr], f"Test failed. Expected {expected_distinct_values[dbAttr]}, but got {result_distinct_values[dbAttr]}"
        print("Distinct values test passed successfully!")


    @staticmethod
    def sort_dbItems_by_dbAttrs(
        dbItems: List[DbItem],
        sort_by_dbAttrs: List[Tuple[DbAttr, DbSortDir]]
    ) -> List[DbItem]:
        """
        Return a list of dbItems sorted according to the given sort_by_dbAttrs.

        :param dbItems: The list of dbItems to sort.
        :param sort_by_dbAttrs: List of tuples containing the attribute to sort by
                                and the direction of sorting (ASC for ascending,
                                DESC for descending).
        :return: A new list of dbItems sorted by the specified attributes.
        """
        sorted_dbItems = dbItems.copy()

        def sort_key(item: DbItem, attr: DbAttr, direction: DbSortDir):
            value = item.get(attr)
            return value if direction == 'ASC' else -value

        for attr, direction in sort_by_dbAttrs:
            sorted_dbItems = sorted(
                sorted_dbItems,
                key=lambda x: sort_key(x, attr, direction)
            )

        return sorted_dbItems

    @staticmethod
    def test_sort_dbItems_by_dbAttrs():
        """
        Test the sort_dbItems_by_dbAttrs function with predefined data.
        """
        # Test data
        test_dbItems = [
            {"name": "Alice", "age": 30, "score": 85},
            {"name": "Bob", "age": 25, "score": 90},
            {"name": "Charlie", "age": 35, "score": 80},
            {"name": "David", "age": 25, "score": 88}
        ]

        # Multiple sort criteria: first by age ascending, then by score descending
        test_sort_by_dbAttrs = [("age", "ASC"), ("score", "DESC")]

        # Expected result after sorting
        expected_sorted_dbItems = [
            {"name": "Bob", "age": 25, "score": 90},
            {"name": "David", "age": 25, "score": 88},
            {"name": "Alice", "age": 30, "score": 85},
            {"name": "Charlie", "age": 35, "score": 80}
        ]

        # Perform sorting
        result = DynamoDbFilterUtils.sort_dbItems_by_dbAttrs(test_dbItems, test_sort_by_dbAttrs)

        # Check if the result matches expected sorted list
        assert result == expected_sorted_dbItems, f"Test failed. Expected {expected_sorted_dbItems}, but got {result}"
        print("Test passed successfully!")

# Running the test
if __name__ == "__main__":
    SortingFunctions.test_sort_dbItems_by_dbAttrs()
