//Print your Name, Section Name and ID
#include <iostream>
#include "Lab8.h"
using namespace std;

void testCopyConstructor(stackType<int> otherStack);
int main()
{
	stackType<int> stack(50);
	stackType<int> copyStack(50);
	stackType<int> dummyStack(100);

	//Initialize stack
	// Set stackTop =  0 in all 3 stacks
	stack.initializeStack(); 
	copyStack.initializeStack();
	dummyStack.initializeStack();

	stack.push(23);
	stack.push(45);	
	//Push 38 to the stack
	stack.push(38);

	copyStack = stack; //copy stack into copyStack 
	cout << "The elements of copyStack: ";
	while (!copyStack.isEmptyStack()) //print copyStack
	{
		cout << copyStack.top() << " ";
		copyStack.pop();
	}

	cout << endl;
	copyStack = stack;

	testCopyConstructor(stack); //test the copy constructor if (!stack.isEmptyStack())
	cout << "The original stack is not empty." << endl
		<< "The top element of the original stack: "
		<< copyStack.top() << endl;

	dummyStack = stack; //copy stack into dummyStack 
	cout << "The elements of dummyStack: ";
	while (!dummyStack.isEmptyStack()) //print dummyStack
	{
		cout << dummyStack.top() << " ";
		dummyStack.pop();
	}
    
	cout << endl;
	system("pause");
	return 0;
}
void testCopyConstructor(stackType<int> otherStack)
{
	if (!otherStack.isEmptyStack())
	{
		cout << "otherStack is not empty." << endl
			<< "The top element of otherStack: "
			<< otherStack.top() << endl;
	}
}