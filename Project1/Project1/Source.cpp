#include<iostream>
#include <cstdio>
#include <iomanip>
using namespace std;
struct nodeType
{
	int info;
	struct nodeType* link;
};
nodeType* buildListForward(int* arr, int size)
{
	nodeType *first = nullptr;
	nodeType *newNode = nullptr;
	nodeType *last = nullptr;;

	first = NULL;
	for (int i = 0; i < size; i++)
	{
		newNode = new nodeType;
		newNode->info = arr[i];
		newNode->link = NULL;
		if (first == NULL)
		{
			first = newNode;
			last = newNode;
		}
		else
		{
			last->link = newNode;
			last = newNode;
		}

	}

	return first;
} 
int main()
{
	const int Size_Array = 5; 
	int ArrayInfo[Size_Array] = { 2,5,8,24,34 };
	//int *ptrArray = nullptr;
	//ptrArray = ArrayInfo;
	cout << "Input" << endl;
	cout << "int Size_Array = " << Size_Array << ";" << endl;
	cout << "int ArrayInfo[" << Size_Array << "] = ";


	//printf("Input\n");
	//printf("int Size_Array = %d;\n", Size_Array);
	//printf("int ArrayInfo[%d] = ", Size_Array);
	bool first = true;
	for (int a : ArrayInfo)
	{
		if (first)
		{
			first = false;
			cout <<"{ "<<a ;
		}
		else
		{
			cout << ", " << a;
		}
	}
	cout << " };";
	/*printf(" };")*/;
	cout << endl << endl;
	cout << "Output" << endl;
	//printf("Output\n");

	nodeType *head, *curr;
	head = buildListForward(ArrayInfo, Size_Array);
	curr = head;
	if (curr)
	{
		cout << "& address of curr pointer " << curr << endl;
		//printf("& address of curr pointer %p \n",curr);
	}
	while (curr != NULL)
	{
		cout << left
			<< setw(10) << "& address of info: "
			<< setw(10) << curr
			<< setw(5) << "INFO: "
			<< setw(5) << curr->info
			<< setw(5) << "LINK"
			<< setw(10) << curr->link << endl;

		//printf("& address of info: %p INFO: %-4d %-4s %p\n", curr, curr->info,"LINK", curr->link);
		curr = curr->link;
	}
	int tmp;
	cin >> tmp;
	return 0;
}