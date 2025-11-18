const Dashboard = () => {
  return (
    <div className="px-4 py-6 sm:px-0">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h2>

      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg font-medium text-gray-900">Welcome to CTIS</h3>
          <div className="mt-2 max-w-xl text-sm text-gray-500">
            <p>
              The Clinical Trial Intelligence Platform helps you predict trial failure risk, identify similar historical trials, and optimize your clinical trial design.
            </p>
          </div>
          <div className="mt-5">
            <p className="text-sm text-gray-500">
              Get started by adding trials or exploring predictions.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
